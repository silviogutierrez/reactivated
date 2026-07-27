import argparse
import atexit
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from uvicorn.config import Config
from uvicorn.server import Server
from uvicorn.supervisors.watchfilesreload import WatchFilesReload

from reactivated_dev.procs import (
    DJANGO_PORT_ENV,
    PROCESSES_ENV,
    RENDERER_ENV,
    VITE_PORT_ENV,
    get_free_port,
    is_serving,
    spawn_tsc,
    spawn_vite,
    terminate_proc,
    wait_for_port,
)

build_mode = False
banner_label = ""
banner_port = 0

# (name, proc, process_group). Core processes (vite/tsc) run in their own
# session and are group-killed; extras stay in our group so they die with the
# terminal and get a plain SIGTERM.
_running: list[tuple[str, subprocess.Popen[bytes], bool]] = []

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
CYAN = "\x1b[36m"
MAGENTA = "\x1b[35m"
RESET = "\x1b[0m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def print_banner(*, compact: bool = False) -> None:
    # DEV_URL / DEV_EXTRA_URLS are optional project-env facts: the canonical
    # dev URL when the project uses something richer than localhost (e.g. a
    # per-worktree hostname for cookie isolation), plus any additional fronts
    # the server is reachable through (e.g. a tailscale serve HTTPS proxy).
    # Without them, plain localhost.
    localhost_url = f"http://localhost:{banner_port}/"
    dev_url = os.environ.get("DEV_URL", localhost_url)
    urls = [dev_url] + ([localhost_url] if dev_url != localhost_url else [])
    urls += os.environ.get("DEV_EXTRA_URLS", "").split()

    if not sys.stdout.isatty():
        print(f"\n  Dev server ({banner_label}): {' '.join(urls)}\n")
        return

    if compact:
        print(f"\n  {MAGENTA}⚡{RESET} {BOLD}{CYAN}{urls[0]}{RESET}\n")
        return

    # The bolt stays out of the box on purpose: emoji render double-width in
    # most terminals, which would skew the padding that keeps the right border
    # aligned. Everything boxed is single-width.
    content = [
        "",
        f"  {BOLD}{MAGENTA}Reactivated{RESET}  {DIM}dev server · {banner_label}{RESET}",
        "",
        *(f"  {BOLD}➜{RESET}  {BOLD}{CYAN}{url}{RESET}" for url in urls),
        "",
    ]
    inner = max(len(ANSI_RE.sub("", line)) for line in content) + 2
    boxed = [
        f"{MAGENTA}┏{'━' * inner}┓{RESET}",
        *(
            f"{MAGENTA}┃{RESET}"
            f"{line}{' ' * (inner - len(ANSI_RE.sub('', line)))}"
            f"{MAGENTA}┃{RESET}"
            for line in content
        ),
        f"{MAGENTA}┗{'━' * inner}┛{RESET}",
    ]
    print("\n" + "\n".join(boxed) + "\n")


def generate_client_assets(*, wait: bool = False) -> None:
    process = subprocess.Popen(
        ["python", "manage.py", "generate_client_assets", "--cached"],
    )
    if wait:
        process.wait()


def build_client() -> None:
    subprocess.run(
        ["npm", "exec", "build.client"],
        env={**os.environ.copy(), "BASE": "/static/dist/"},
        check=True,
    )


def spawn_extras() -> None:
    commands = [
        stripped
        for line in os.environ.get(PROCESSES_ENV, "").splitlines()
        if (stripped := line.strip())
    ]
    if not commands:
        return

    for command in commands:
        # shell=True so $VARs resolve at spawn time — including the runtime
        # ports this process exported just before calling here.
        proc = subprocess.Popen(command, shell=True)
        _running.append((command, proc, False))

    # An extra holding a contended resource (a DB tunnel whose port another
    # worktree's tunnel already holds) exits immediately. That's fine while the
    # other one lives, so warn instead of dying.
    time.sleep(2)
    for command, proc, _ in _running:
        if proc.poll() is not None:
            print(
                f"WARNING: extra process exited immediately "
                f"(code={proc.returncode}): {command}"
            )


def cleanup() -> None:
    print("Running atexit cleanup…")
    for name, proc, process_group in reversed(_running):
        if proc.poll() is None:
            print(f"Terminating {name}…")
            try:
                terminate_proc(proc, process_group=process_group)
            except Exception as e:  # noqa: BLE001
                print(f"Error while terminating {name}: {e!r}")
        else:
            print(f"Process {name} already terminated (code={proc.returncode})")
    print("Cleanup done.")


class SmartChangeReload(WatchFilesReload):
    def should_restart(self) -> list[Path] | None:
        changes = super().should_restart()

        if changes:
            print(f"Changes detected: {changes}")
            if build_mode:
                generate_client_assets(wait=True)
                build_client()
            else:
                generate_client_assets()
            # Reprint so the URL survives long sessions: compact on purpose, a
            # full banner on every save would drown the output being watched.
            print_banner(compact=True)
        return changes


def main() -> None:
    global build_mode, banner_label, banner_port

    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()

    # A console script doesn't put cwd on sys.path the way `python file.py`
    # does; the project's server.asgi (resolved in the reload worker, which
    # inherits this path) needs it.
    sys.path.insert(0, os.getcwd())

    # The user-facing port. In vite mode Vite listens here and proxies to
    # Django; in build mode Django serves the built assets here directly.
    # Shell-owned static allocation: setup_environment.sh derives and exports
    # a stable per-checkout value; export DEBUG_PORT yourself to override.
    if "DEBUG_PORT" not in os.environ:
        sys.exit(
            "reactivate: DEBUG_PORT is not set — source "
            "setup_environment.sh (which derives and exports it), or export "
            "DEBUG_PORT yourself."
        )
    user_port = int(os.environ["DEBUG_PORT"])

    # A live server here means another instance (usually another worktree) owns
    # the port. Vite mode cannot detect this on its own: the express server
    # binds a wildcard socket that macOS lets coexist with an existing specific
    # bind, so the loser "starts" cleanly but never receives traffic. Error out
    # like Django's runserver would. This also keeps wait_for_port honest — a
    # port verified free here can only have been opened by our own vite.
    if is_serving(user_port):
        sys.exit(
            f"reactivate: port {user_port} is already serving — another "
            "worktree's dev server? Stop it or change DEBUG_PORT."
        )

    atexit.register(cleanup)

    reload_includes: list[str] = []

    if args.build:
        # Build mode: no Vite dev server. Run a full production build and let
        # Django serve the bundled assets, so a page load is a handful of
        # requests instead of Vite's hundreds of unbundled modules. On change we
        # rebuild. Slower per change and no HMR, but reliable behind a proxy.
        build_mode = True
        backend_port = user_port
        os.environ[DJANGO_PORT_ENV] = str(backend_port)
        spawn_extras()
        generate_client_assets(wait=True)
        build_client()
        # Build mode needs client/ watched: reload_includes only filters events,
        # the rebuild depends on the frontend tree actually being watched.
        reload_dirs = ["server", "client"]
        reload_includes = ["*.tsx", "*.ts", "*.css"]
        label = "build mode"
    else:
        backend_port = get_free_port()
        os.environ[VITE_PORT_ENV] = str(user_port)
        os.environ[DJANGO_PORT_ENV] = str(backend_port)
        os.environ[RENDERER_ENV] = f"http://localhost:{user_port}"
        spawn_extras()
        generate_client_assets(wait=False)

        vite_proc = spawn_vite(base="/static/")
        _running.append(("vite", vite_proc, True))
        # Block until Vite is actually listening (it proxies user_port) rather
        # than guessing with a sleep; fails loudly if Vite dies on boot.
        # Generous timeout: the first run does dependency pre-bundling.
        wait_for_port("vite", vite_proc, user_port, timeout=60)
        # Never the worktree root: an unscoped reload watcher registers a
        # recursive FSEvents watch over node_modules/.git and melts fseventsd
        # (reload_excludes filters events post-hoc, it does not shrink the
        # OS-level watch).
        reload_dirs = ["server"]
        label = "vite"

    tsc_proc = spawn_tsc()
    _running.append(("tsc", tsc_proc, True))

    banner_label = label
    banner_port = user_port
    print_banner()

    config = Config(
        "reactivated_dev.asgi:create_application",
        host="127.0.0.1",
        factory=True,
        reload=True,
        port=backend_port,
        log_level="info",
        timeout_graceful_shutdown=0,
        reload_dirs=reload_dirs,
        reload_excludes=[
            "server/**/tests/**",
            "server/**/pytests.py",
        ],
        reload_includes=reload_includes,
    )
    server = Server(config)
    sock = config.bind_socket()
    SmartChangeReload(config, target=server.run, sockets=[sock]).run()
