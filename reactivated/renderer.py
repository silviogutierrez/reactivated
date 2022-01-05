import atexit
import logging
import re
import subprocess
import sys
import urllib.parse
from typing import Any, List, Optional

import simplejson
from django.conf import settings
from django.http import HttpRequest
from django.template.defaultfilters import escape

import requests_unixsocket

from . import constants

renderer_process_port: Optional[str] = None
logger = logging.getLogger("django.server")

# client_process =
# server_process =
# maybe_render_process =


def wait_and_get_port() -> Optional[str]:
    global renderer_process_port

    if renderer_process_port is not None:
        return renderer_process_port

    logger.info("Starting render process")
    entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])
    process = subprocess.Popen(
        ["node", "./node_modules/.bin/server.js", *entry_points],
        encoding="utf-8",
        stdout=subprocess.PIPE,
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

        if match := re.match(r"RENDERER:([/.\w]+):LISTENING", output):
            renderer_process_port = match.group(1)
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
    data = simplejson.dumps(payload)
    headers = {"Content-Type": "application/json"}

    if "debug" in request.GET:
        return f"<html><body><h1>Debug response</h1><pre>{escape(data)}</pre></body></html>"
    elif (
        respond_with_json
        or "raw" in request.GET
        or getattr(settings, "REACTIVATED_SERVER", False) is None
    ):
        request._is_reactivated_response = True  # type: ignore[attr-defined]
        return data

    renderer_port = wait_and_get_port()

    session = requests_unixsocket.Session()
    socket = urllib.parse.quote_plus(
        renderer_port,
    )

    response = session.post(f"http+unix://{socket}", headers=headers, data=data)

    if response.status_code == 200:
        return response.text
    else:
        raise Exception(response.json()["stack"])
