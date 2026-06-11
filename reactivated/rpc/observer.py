from __future__ import annotations

import enum
from typing import Any, Callable, Coroutine, Literal

from django.http import HttpRequest


class RequestStatus(enum.Enum):
    ERROR = "ERROR"
    MALFORMED = "MALFORMED"
    INVALID = "INVALID"
    SUCCESS = "SUCCESS"


RPCObserverFunc = Callable[
    [
        HttpRequest,  # request
        str,  # rpc_name
        Literal["errors"] | bool,  # log
        RequestStatus,  # status
        Any,  # input
        Any,  # output
        bytes | None,  # body
        BaseException | None,  # exception
    ],
    Coroutine[Any, Any, None],
]

_observer: RPCObserverFunc | None = None


def rpc_observer(fn: RPCObserverFunc) -> RPCObserverFunc:
    global _observer
    _observer = fn
    return fn


def get_observer() -> RPCObserverFunc | None:
    return _observer
