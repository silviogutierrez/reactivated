import atexit
import os
import re
import signal
import subprocess
from typing import Any

from django.conf import settings


def terminate_proc(proc: subprocess.Popen[Any]) -> None:
    """
    npm exec doesn't correctly forward signals to its child processes. So,
    simply calling proc.terminate() doesn't actually kill the process. Rather,
    we have to send SIGTERM to the entire process group.

    Note: using this requires that the initial call to subprocess.Popen included
    the `start_new_session=True` flag.
    """
    pgrp = os.getpgid(proc.pid)
    os.killpg(pgrp, signal.SIGTERM)
    proc.communicate(timeout=5)


def start_tsc() -> None:
    tsc_process = subprocess.Popen(
        ["npm", "exec", "tsc", "--", "--watch", "--noEmit", "--preserveWatchOutput"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        start_new_session=True,
        env={**os.environ.copy()},
    )
    atexit.register(lambda: terminate_proc(tsc_process))


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
        start_new_session=True,
        env={**os.environ.copy()},
    )
    atexit.register(lambda: terminate_proc(client_process))


def start_renderer() -> None:
    if os.environ.get("REACTIVATED_RENDERER", None):
        return

    os.environ["REACTIVATED_RENDERER"] = "true"

    renderer_process = subprocess.Popen(
        ["npm", "exec", "build.renderer"],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        start_new_session=True,
        env={
            **os.environ.copy(),
        },
    )
    atexit.register(lambda: terminate_proc(renderer_process))

    renderer_process_port = ""
    output = ""

    for c in iter(lambda: renderer_process.stdout.read(1), b""):  # type: ignore[union-attr]
        output += c

        if match := re.match(r"RENDERER:([/.\w]+):LISTENING", output):
            renderer_process_port = match.group(1)
            break
    os.environ["REACTIVATED_RENDERER"] = renderer_process_port
