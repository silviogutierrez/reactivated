import atexit
import json
import os
import re
import subprocess
from typing import Any, TypedDict

import psutil
from django.conf import settings


class ServeOptions(TypedDict):
    host: str
    port: int


def terminate_proc(proc: subprocess.Popen[Any]) -> None:
    """
    npm exec doesn't correctly forward signals to its child processes. So,
    simply calling proc.terminate() doesn't actually kill the process. Rather,
    we have to recursively iterate and kill each individual child proc.
    """
    parent = psutil.Process(proc.pid)
    for child in parent.children(recursive=True):
        child.terminate()
    parent.terminate()
    proc.communicate(timeout=5)


def start_tsc() -> None:
    tsc_process = subprocess.Popen(
        ["npm", "exec", "tsc", "--", "--watch", "--noEmit", "--preserveWatchOutput"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        env={**os.environ.copy()},
    )
    atexit.register(lambda: terminate_proc(tsc_process))


def start_client(serve_opts: ServeOptions) -> None:
    entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

    client_process = subprocess.Popen(
        [
            "npm",
            "exec",
            "build.client",
            "--",
            json.dumps(serve_opts),
            *entry_points,
        ],
        stdout=subprocess.PIPE,
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
