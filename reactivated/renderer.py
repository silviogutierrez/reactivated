import atexit
import logging
import os
import re
import subprocess
import urllib.parse
from typing import Any, List, Optional

import requests_unixsocket  # type: ignore[import]
import simplejson
from django.conf import settings
from django.http import HttpRequest
from django.template.defaultfilters import escape

renderer_process_port: Optional[str] = None
logger = logging.getLogger("django.server")


def wait_and_get_port() -> str:
    if renderer := os.environ.get("REACTIVATED_RENDERER", None):
        return renderer

    global renderer_process_port

    if renderer_process_port is not None:
        return renderer_process_port

    renderer_process = subprocess.Popen(
        [
            "node",
            f"{settings.BASE_DIR}/node_modules/_reactivated/renderer.js",
        ],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        cwd=settings.BASE_DIR,
    )
    atexit.register(lambda: renderer_process.terminate())

    output = ""

    for c in iter(lambda: renderer_process.stdout.read(1), b""):  # type: ignore[union-attr]
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

    # Sometimes we are running tests and the CWD is outside BASE_DIR.  For
    # example, the reactivated tests themselves.  Instead of using BASE_DIR as
    # the prefix, we calculate the relative path to avoid the 100 character
    # UNIX socket limit.
    # But dots do not work for relative paths with sockets so we clear it.
    rel_path = os.path.relpath(settings.BASE_DIR)
    address = renderer_port if rel_path == "." else f"{rel_path}/{renderer_port}"

    session = requests_unixsocket.Session()
    socket = urllib.parse.quote_plus(address)

    response = session.post(f"http+unix://{socket}", headers=headers, data=data)

    if response.status_code == 200:
        return response.text  # type: ignore[no-any-return]
    else:
        raise Exception(response.json()["stack"])
