import atexit
import os
import re
import subprocess

from django.conf import settings
from .config import build_client_config


def start_config_build() -> None:
    # Other processes depend on this, so block until the build to completes
    # once, then start the background watcher
    tsc_process = build_client_config(watch=False, stdout=subprocess.PIPE)
    if tsc_process is None:
        # Custom project config must not exist
        return
    tsc_process.communicate()
    if tsc_process.returncode != 0:
        raise RuntimeError(
            f"TypeScript error. Failed to compile {client_config_src_path}"
        )
    tsc_process = build_client_config(watch=True)
    atexit.register(lambda: tsc_process.terminate())


def start_tsc() -> None:
    tsc_process = subprocess.Popen(
        ["npm", "exec", "tsc", "--", "--watch", "--noEmit", "--preserveWatchOutput"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        env={**os.environ.copy()},
    )
    atexit.register(lambda: tsc_process.terminate())


def start_client() -> None:
    entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

    client_process = subprocess.Popen(
        [
            "npm",
            "exec",
            "build.client",
            "--",
            *entry_points,
        ],
        stdout=subprocess.PIPE,
        env={**os.environ.copy()},
    )
    atexit.register(lambda: client_process.terminate())


def start_renderer() -> None:
    os.environ["REACTIVATED_RENDERER"] = "true"

    renderer_process = subprocess.Popen(
        ["npm", "exec", "build.renderer"],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        env={
            **os.environ.copy(),
        },
    )
    atexit.register(lambda: renderer_process.terminate())

    renderer_process_port = ""
    output = ""

    for c in iter(lambda: renderer_process.stdout.read(1), b""):  # type: ignore[union-attr]
        output += c

        if match := re.match(r"RENDERER:([/.\w]+):LISTENING", output):
            renderer_process_port = match.group(1)
            break
    os.environ["REACTIVATED_RENDERER"] = renderer_process_port
