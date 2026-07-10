from __future__ import annotations

from typing import Annotated, Any, Callable, Literal, get_type_hints

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
from pydantic import BeforeValidator, create_model, model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler

from .rpc.core import LazyStr, Pick


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


class SafeUser(Pick):
    """The safe default shape for ``django.contrib.auth``'s context
    processor: the user's own identity, nothing more. No email (keep PII
    out of rendered props by default), no perms (PermWrapper is a lazy,
    query-bearing proxy). Override by registering a replacement Pick via
    ``register_processor_type`` — or skip Django's processor and write
    your own, which supersedes this entirely."""

    # None covers unsaved/phantom users (authenticated but never persisted).
    id: int | str | None
    username: str
    is_authenticated: bool
    is_staff: bool

    @model_validator(mode="wrap")  # type: ignore[arg-type]
    @classmethod
    def _accept_user(
        cls, values: Any, handler: ModelWrapValidatorHandler["SafeUser"]
    ) -> "SafeUser":
        user = values
        if hasattr(user, "is_authenticated"):
            return cls(
                id=user.pk,
                username=user.get_username(),
                is_authenticated=True,
                is_staff=bool(getattr(user, "is_staff", False)),
            )
        return handler(values)


def _resolve_auth_user(value: Any) -> Any:
    # Processor dicts are flattened into one context, so resolution happens
    # at the field: unwrap the lazy user, map anonymous to None.
    if isinstance(value, LazyObject):
        value = value.__reduce__()[1][0]
    if value is None or not getattr(value, "is_authenticated", False):
        return None
    return value


class AuthProcessor(Pick):
    user: Annotated[SafeUser | None, BeforeValidator(_resolve_auth_user)]


def register_processor_type(processor_path: str, pick: type[Pick]) -> None:
    """Override the typed shape for a context processor (usually one of
    Django's untyped builtins)."""
    TYPE_HINTS[processor_path] = {"return": pick}


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
    "django.contrib.auth.context_processors.auth": {"return": AuthProcessor},
}


def get_annotation_or_type_hints(item: Any) -> dict[str, Any]:
    override_name = f"{item.__module__}.{item.__qualname__}"
    if override := TYPE_HINTS.get(override_name, None):
        return override
    return get_type_hints(item)


_context_processors: list[Callable[[HttpRequest], dict[str, Any]]] | None = None
_context_processor_paths: list[str] | None = None


def get_context_processor_paths() -> list[str]:
    """Context processors come from the stock ``DjangoTemplates`` entry —
    the exact block ``startproject`` generates. No custom backend, no
    custom setting."""
    global _context_processor_paths
    if _context_processor_paths is None:
        for template_config in settings.TEMPLATES:
            config: dict[str, Any] = template_config
            if (
                config.get("BACKEND")
                == "django.template.backends.django.DjangoTemplates"
            ):
                _context_processor_paths = config.get("OPTIONS", {}).get(
                    "context_processors", []
                )
                break
        else:
            raise ImproperlyConfigured(
                "reactivated: no django.template.backends.django.DjangoTemplates "
                "entry in settings.TEMPLATES — templates render with context "
                "processors taken from that entry's OPTIONS"
            )
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
