import os
import signal
import socket
import subprocess
import time
from collections.abc import Mapping
from typing import Any

# The port-coordination contract between the outer supervisor (reactivate or the
# patched runserver) and the inner Django process. Extra processes declared in
# PROCESSES_ENV may reference these names too: they are exported before extras
# spawn, so `$REACTIVATED_DJANGO_PORT` in a command line resolves at spawn time.
# Build mode has no vite, so only DJANGO_PORT_ENV is exported there — an extra
# that must work in both modes should reference DEBUG_PORT or DJANGO_PORT_ENV.
VITE_PORT_ENV = "REACTIVATED_VITE_PORT"
DJANGO_PORT_ENV = "REACTIVATED_DJANGO_PORT"
RENDERER_ENV = "REACTIVATED_RENDERER"
PROCESSES_ENV = "REACTIVATED_DEV_PROCESSES"
# Set by whatever *runs* the dev server — a preview supervisor, a container
# entrypoint — rather than by the project itself. Kept separate so a project
# can own PROCESSES_ENV with the obvious semantics (append its own lines, clear
# it on re-entry to stay idempotent) without those writes dropping a side-car
# the caller injected. A project should never write this one.
PROCESSES_EXTRA_ENV = "REACTIVATED_DEV_PROCESSES_EXTRA"


def get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("", 0))
        return int(sock.getsockname()[1])


def is_serving(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def is_socket_serving(path: str) -> bool:
    """
    Whether a live process is accepting on `path`. A socket file left behind by
    a crashed run still exists but refuses connections, so existence alone
    cannot answer "is someone already serving here?".
    """
    if not os.path.exists(path):
        return False

    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(path) == 0


def parse_processes(raw: str) -> list[str]:
    """
    One command per line, blank lines dropped, duplicates collapsed (first
    occurrence wins, order preserved).

    PROCESSES_ENV is *exported*, so it crosses shell boundaries: a project's env
    setup that appends its own lines will re-append them on every nested shell
    entry, and an outer caller (a preview supervisor, a container entrypoint)
    may have injected a line of its own that the project's setup then inherits.
    Collapsing duplicates makes both harmless, so a project can seed from the
    inherited value rather than clearing it — clearing is what silently drops an
    injected side-car.
    """
    seen: set[str] = set()
    commands: list[str] = []

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            commands.append(stripped)

    return commands


def collect_processes(environ: Mapping[str, str]) -> list[str]:
    """
    Every side-car to spawn: the caller's injected ones first, then the
    project's own.

    Two variables so neither party has to know about the other. The project
    keeps the plain PROCESSES_ENV API and may clear or rebuild it freely — the
    natural way to stay idempotent when its own setup re-runs on nested shell
    entry — and an injected side-car survives that regardless, because it lives
    in the variable the project never touches.
    """
    return parse_processes(
        "\n".join(
            [environ.get(PROCESSES_EXTRA_ENV, ""), environ.get(PROCESSES_ENV, "")]
        )
    )


def terminate_proc(proc: subprocess.Popen[Any], *, process_group: bool = True) -> None:
    """
    npm exec / npx don't reliably forward signals to their children, so
    proc.terminate() may leave grandchildren alive. We SIGTERM the whole
    process group instead — which requires the Popen() call to have used
    start_new_session=True.

    For a child sharing our own group (an extra spawned without
    start_new_session, so it dies with the terminal), pass process_group=False:
    killpg there would signal the supervisor itself.
    """
    if not process_group:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return

    try:
        pgrp = os.getpgid(proc.pid)
    except ProcessLookupError:
        return

    os.killpg(pgrp, signal.SIGTERM)
    try:
        proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def spawn_vite(*, base: str) -> subprocess.Popen[bytes]:
    proc = subprocess.Popen(
        ["npm", "exec", "start_vite"],
        env={**os.environ.copy(), "BASE": f"{base}dist/"},
        start_new_session=True,
    )
    # npm exec is weird and seems to run into duplicate issues if executed
    # too quickly. There are better ways to do this, I assume.
    time.sleep(0.5)
    return proc


def spawn_tsc() -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        ["npm", "exec", "tsc", "--", "--watch", "--noEmit", "--preserveWatchOutput"],
        env={**os.environ.copy()},
        start_new_session=True,
    )


def wait_for_port(
    name: str, proc: subprocess.Popen[bytes], port: int, *, timeout: float
) -> None:
    """
    Block until `port` accepts a TCP connection, instead of guessing with a
    sleep. Fails loudly if the process dies first.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"{name} exited (code={proc.returncode}) before port {port} was ready"
            )
        if is_serving(port):
            return
        time.sleep(0.1)

    raise TimeoutError(f"{name} did not open port {port} within {timeout}s")
