from __future__ import annotations

from typing import Any, Callable, Literal, get_type_hints

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string
from pydantic import create_model, model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler

from .core import LazyStr, Pick


class Request(Pick):
    path: str
    url: str
    csp_nonce: str | None

    @model_validator(mode="wrap")  # type: ignore[arg-type]
    @classmethod
    def _accept_http_request(
        cls, values: Any, handler: ModelWrapValidatorHandler["Request"]
    ) -> "Request":
        if isinstance(values, HttpRequest):
            return cls(
                path=values.path,
                url=values.build_absolute_uri(),
                csp_nonce=getattr(values, "csp_nonce", None),
            )
        return handler(values)


class RequestProcessor(Pick):
    request: Request


class Message(Pick):
    level_tag: Literal["info", "success", "error", "warning", "debug"]
    message: str
    level: int
    from_server: bool = True


class MessagesProcessor(Pick):
    messages: list[Message]


class CSRFProcessor(Pick):
    csrf_token: LazyStr


class BaseContext(Pick):
    template_name: str


class StaticProcessor(Pick):
    STATIC_URL: str


TYPE_HINTS: dict[str, dict[str, type[Pick]]] = {
    "django.template.context_processors.request": {"return": RequestProcessor},
    "django.template.context_processors.csrf": {"return": CSRFProcessor},
    "django.template.context_processors.static": {"return": StaticProcessor},
    "django.contrib.messages.context_processors.messages": {
        "return": MessagesProcessor
    },
}


def get_annotation_or_type_hints(item: Any) -> dict[str, Any]:
    override_name = f"{item.__module__}.{item.__qualname__}"
    if override := TYPE_HINTS.get(override_name, None):
        return override
    return get_type_hints(item)


_context_processors: list[Callable[[HttpRequest], dict[str, Any]]] | None = None
_context_processor_paths: list[str] | None = None


def get_context_processor_paths() -> list[str]:
    global _context_processor_paths
    if _context_processor_paths is None:
        _context_processor_paths = []
        for template_config in settings.TEMPLATES:
            config: dict[str, Any] = template_config
            if config.get("BACKEND") == "reactivated.backend.JSX":
                _context_processor_paths = config.get("OPTIONS", {}).get(
                    "context_processors", []
                )
                break
    return _context_processor_paths


def get_context_processors() -> list[Callable[[HttpRequest], dict[str, Any]]]:
    global _context_processors
    if _context_processors is None:
        _context_processors = [
            import_string(path) for path in get_context_processor_paths()
        ]
    return _context_processors


def get_context_class() -> type[Pick]:
    context_processors: list[str] = get_context_processor_paths()

    all_fields: dict[str, Any] = {}

    for field_name, field_type in get_type_hints(BaseContext).items():
        all_fields[field_name] = (field_type, ...)

    for processor_path in context_processors:
        definition = import_string(processor_path)
        annotations = get_annotation_or_type_hints(definition)
        annotation = annotations.get("return", None)
        assert annotation, f"No return annotation for {processor_path}"

        type_hints = get_type_hints(annotation)
        for field_name, field_type in type_hints.items():
            all_fields[field_name] = (field_type, ...)

    Context = create_model("Context", __base__=Pick, **all_fields)
    return Context
