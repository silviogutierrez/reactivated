import atexit
import os
import re
import socket
import subprocess

from django.conf import settings


def start_tsc() -> None:
    tsc_process = subprocess.Popen(
        ["npm", "exec", "tsc", "--", "--watch", "--noEmit", "--preserveWatchOutput"],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        env={**os.environ.copy()},
    )
    atexit.register(lambda: tsc_process.terminate())


def start_client() -> None:
    sock = socket.socket()
    sock.bind(("", 0))
    free_port = str(sock.getsockname()[1])

    entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

    client_process = subprocess.Popen(
        [
            "npm",
            "exec",
            "vite",
            "--",
            "--force",
            "--port",
            free_port,
        ],
        stdout=subprocess.PIPE,
        env={**os.environ.copy()},
    )
    os.environ["REACTIVATED_CLIENT_PORT"] = free_port
    atexit.register(lambda: client_process.terminate())


def start_renderer() -> None:
    os.environ["REACTIVATED_RENDERER"] = "true"

    renderer_process = subprocess.Popen(
        ["npm", "exec", "build.renderer.js"],
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
