import atexit
import logging
import re
import subprocess
import sys
from typing import Any, List, Optional

import requests
import simplejson
from django.conf import settings
from django.http import HttpRequest
from django.template.defaultfilters import escape

renderer_process_port = None
logger = logging.getLogger("django.server")


def wait_and_get_port() -> Optional[int]:
    global renderer_process_port

    if renderer_process_port is not None:
        return renderer_process_port

    renderer_command = (
        ["node", "node_modules/reactivated/renderer.js",]
        if settings.DEBUG is False
        else [
            "node_modules/.bin/babel-node",
            "--extensions",
            ".ts,.tsx",
            "node_modules/reactivated/renderer.js",
        ]
    )

    logger.info("Starting render process")

    process = subprocess.Popen(
        renderer_command, encoding="utf-8", stdout=subprocess.PIPE,
    )

    def cleanup() -> None:
        # Pytest has issues with this, see https://github.com/pytest-dev/pytest/issues/5502
        # We can't use the env variable PYTEST_CURRENT_TEST because this happens
        # after running all tests and closing the session.
        # See: https://stackoverflow.com/questions/25188119/test-if-code-is-executed-from-within-a-py-test-session
        if "pytest" not in sys.modules:
            logger.info("Cleaning up renderer process")
        process.terminate()

    atexit.register(cleanup)

    output = ""

    for c in iter(lambda: process.stdout.read(1), b""):  # type: ignore[union-attr]
        output += c

        if match := re.match(r"RENDERER:([\d]+):LISTENING", output):
            renderer_process_port = int(match.group(1))
            return renderer_process_port
    assert False, "Could not bind to renderer"


def get_accept_list(request: HttpRequest) -> List[str]:
    """
    Given the incoming request, return a tokenized list of media
    type strings.

    From https://github.com/encode/django-rest-framework/blob/master/rest_framework/negotiation.py
    """
    header = request.META.get("HTTP_ACCEPT", "*/*")
    return [token.strip() for token in header.split(",")]


def should_respond_with_json(request: HttpRequest) -> bool:
    accepts = get_accept_list(request)

    return request.GET.get("format", None) == "json" or any(
        ["application/json" in content_type for content_type in accepts]
    )


def render_jsx_to_string(request: HttpRequest, context: Any, props: Any) -> str:
    respond_with_json = should_respond_with_json(request)

    payload = {"context": context, "props": props}
    data = simplejson.dumps(payload, indent=4)
    headers = {"Content-Type": "application/json"}

    if "debug" in request.GET:
        return f"<html><body><h1>Debug response</h1><pre>{escape(data)}</pre></body></html>"
    elif (
        respond_with_json or "raw" in request.GET or settings.REACTIVATED_SERVER is None
    ):
        request._is_reactivated_response = True  # type: ignore[attr-defined]
        return data

    renderer_port = wait_and_get_port()

    response = requests.post(
        f"http://localhost:{renderer_port}", headers=headers, data=data
    )

    if response.status_code == 200:
        return response.text
    else:
        raise Exception(response.json()["stack"])
