from typing import Any


class HttpRequest(object):
    GET: Any
    POST: Any
    FILES: Any
    method: str
    path: str
