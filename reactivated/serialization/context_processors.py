from typing import Any, List, Literal, NamedTuple, Optional, Type, get_type_hints

from django.http import HttpRequest
from django.utils.module_loading import import_string

from . import Intersection, serialize
from .registry import JSON, Thing


class Request(NamedTuple):
    path: str
    url: str

    # If django-csp is in use, include the CSP nonce for the request
    # See https://django-csp.readthedocs.io/en/latest/nonce.html#using-the-generated-csp-nonce
    csp_nonce: Optional[str]

    @classmethod
    def get_serialized_value(
        Type: Type["Request"], value: HttpRequest, schema: Thing
    ) -> JSON:
        serialized = serialize(value, schema, suppress_custom_serializer=True)

        return {
            **serialized,
            "url": value.build_absolute_uri(),
        }


class RequestProcessor(NamedTuple):
    request: Request


class Message(NamedTuple):
    level_tag: Literal["info", "success", "error", "warning", "debug"]
    message: str

    # TODO: should this be removed? Kind of useless.
    level: int

    # TODO: document
    from_server: bool = True


class MessagesProcessor(NamedTuple):
    messages: List[Message]


class CSRFProcessor(NamedTuple):
    csrf_token: str


class BaseContext(NamedTuple):
    template_name: str


class StaticProcessor(NamedTuple):
    STATIC_URL: str


TYPE_HINTS = {
    "django.template.context_processors.request": {"return": RequestProcessor},
    "django.template.context_processors.csrf": {"return": CSRFProcessor},
    "django.template.context_processors.static": {"return": StaticProcessor},
    "django.contrib.messages.context_processors.messages": {
        "return": MessagesProcessor
    },
}


def get_annotation_or_type_hints(item: Any) -> Any:
    override_name = f"{item.__module__}.{item.__qualname__}"

    if override := TYPE_HINTS.get(override_name, None):
        return override
    return get_type_hints(item)


def create_context_processor_type(context_processors: List[str]) -> Any:
    types = [BaseContext]

    for context_processor in context_processors:
        definition = import_string(context_processor)
        annotations = get_annotation_or_type_hints(definition)

        annotation = annotations.get("return", None)
        assert (
            annotation
        ), f"No annotations found for context processor {context_processor}"
        types.append(annotation)

    return Intersection[types]  # type: ignore[misc]
