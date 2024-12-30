import abc
import atexit
import enum
import inspect
import os
import signal
import socket
import subprocess
import time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from django import forms as django_forms
from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.core.management.commands import runserver
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, URLResolver
from mypy_extensions import Arg, KwArg

from .backend import JSX as JSX  # noqa: F401
from .models import computed_foreign_key as computed_foreign_key  # noqa: F401
from .models import computed_relation as computed_relation  # noqa: F401
from .pick import BasePickHolder
from .pick import Pick as Pick  # noqa: F401
from .serialization import registry
from .stubs import _GenericAlias
from .templates import Action as Action  # noqa: F401
from .templates import interface as interface  # noqa: F401
from .templates import template as template  # noqa: F401


def terminate_proc(proc: subprocess.Popen[Any]) -> None:
    """
    npm exec doesn't correctly forward signals to its child processes. So,
    simply calling proc.terminate() doesn't actually kill the process. Rather,
    we have to send SIGTERM to the entire process group.
    Note: using this requires that the initial call to subprocess.Popen included
    the `start_new_session=True` flag.
    """
    try:
        pgrp = os.getpgid(proc.pid)
    except ProcessLookupError:
        pass
    else:
        os.killpg(pgrp, signal.SIGTERM)
        proc.communicate(timeout=5)


original_run = runserver.Command.run


generate_callbacks: List[Any] = []


class GenerateFunction(Protocol):
    def __call__(self, *, skip_cache: bool = False) -> None: ...


def generate(function: GenerateFunction) -> None:
    generate_callbacks.append(function)


def run_generations(skip_cache: bool = False) -> None:
    if "REACTIVATED_SKIP_GENERATIONS" in os.environ:
        return

    for generate_callback in generate_callbacks:
        generate_callback(skip_cache)

    from .apps import generate_schema

    generate_schema(skip_cache)


def get_free_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    free_port = sock.getsockname()[1]
    return free_port  # type: ignore[no-any-return]


def outer_process(cmd: Any) -> None:
    if os.environ.get("REACTIVATED_RENDERER") is not None:
        os.environ["REACTIVATED_SKIP_SERVER"] = "true"
        return

    free_port = get_free_port()
    original_port = cmd.port

    # Lie to the terminal when logging the port we bound to, so the user still
    # visits the original port.
    class LyingPort(int):
        def __str__(self) -> str:
            return str(original_port)

    cmd.port = LyingPort(free_port)

    os.environ["REACTIVATED_VITE_PORT"] = original_port
    os.environ["REACTIVATED_DJANGO_PORT"] = str(free_port)

    run_generations()

    vite_process = subprocess.Popen(
        ["npm", "exec", "start_vite"],
        # stdout=subprocess.PIPE,
        env={**os.environ.copy(), "BASE": f"{settings.STATIC_URL}dist/"},
        start_new_session=True,
    )
    atexit.register(lambda: terminate_proc(vite_process))
    # npm exec is weird and seems to run into duplicate issues if executed
    # too quickly. There are better ways to do this, I assume.
    time.sleep(0.5)

    tsc_process = subprocess.Popen(
        [
            "npm",
            "exec",
            "tsc",
            "--",
            "--watch",
            "--noEmit",
            "--preserveWatchOutput",
        ],
        # stdout=subprocess.PIPE,
        env={**os.environ.copy()},
        start_new_session=True,
    )
    atexit.register(lambda: terminate_proc(tsc_process))

    os.environ["REACTIVATED_RENDERER"] = f"http://localhost:{cmd.port}"


def inner_process(cmd: Any) -> None:
    # Inner process still needs this rebound for Django's built in runserver
    # though maybe not for django_extensions runserver_plus
    free_port = os.environ["REACTIVATED_DJANGO_PORT"]
    original_port = os.environ["REACTIVATED_VITE_PORT"]

    class LyingPort(int):
        def __str__(self) -> str:
            return str(original_port)

    cmd.port = LyingPort(free_port)

    run_generations()


def patched_run(self: Any, **options: Any) -> Any:
    if (os.environ.get("RUN_MAIN") == "true") and os.environ.get(
        "REACTIVATED_SKIP_SERVER"
    ) != "true":
        original_on_bind = runserver.Command.on_bind

        def on_bind(self: Any, server_port: Any) -> None:
            original_on_bind(self, int(os.environ["REACTIVATED_VITE_PORT"]))

        runserver.Command.on_bind = on_bind  # type: ignore[method-assign]

        inner_process(self)
    else:
        outer_process(self)

    return original_run(self, **options)


runserver.Command.run = patched_run  # type: ignore[method-assign]

# Mypy tests have problems with this executing outside a Django context so
# we skip the patching on those runs.
if "MYPY_CONFIG_FILE_DIR" not in os.environ:
    try:
        from django_extensions.management.commands import (  # type: ignore[import-untyped]
            runserver_plus,
        )

        original_run_plus = runserver_plus.Command.inner_run
    except ImportError:
        pass
    else:

        def patched_run_plus(self: Any, options: Any) -> Any:
            if (os.environ.get("WERKZEUG_RUN_MAIN") == "true") and os.environ.get(
                "REACTIVATED_SKIP_SERVER"
            ) != "true":
                inner_process(self)
            else:
                outer_process(self)

            return original_run_plus(self, options)

        runserver_plus.Command.inner_run = patched_run_plus


def export(var: Any) -> None:
    if inspect.isclass(var) and issubclass(var, enum.Enum):
        name = f"{var.__module__}.{var.__qualname__}"
        registry.value_registry.update({name: (var, "enum")})
        return

    """See: https://stackoverflow.com/a/18425523"""
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()  # type: ignore[union-attr]
    name = [var_name for var_name, var_val in callers_local_vars if var_val is var][0]

    registry.value_registry.update({name: (var, "primitive")})


# def export_type(var: Any) -> None:
#     from django.apps import apps
#     callers_local_vars = inspect.currentframe().f_back.f_locals.items()  # type: ignore[union-attr]
#     name = [var_name for var_name, var_val in callers_local_vars if var_val is var][0]
#
#     frm = inspect.stack()[1]
#     mod = inspect.getmodule(frm[0])
#     pick_name = name
#
#     definition_name = None
#
#     for app_config in apps.get_app_configs():
#         if app_config.name in mod.__name__:
#             relative_module = mod.__name__.replace(f"{app_config.name}.", "")
#             definition_name = f"{app_config.label}.{relative_module}.{pick_name}"
#             break
#     else:
#         assert False, "Could not determine name for export"
#
#     from .serialization import create_schema
#
#     schema  = create_schema(var, {})
#
#     if registry.global_types["models"] is registry.DefaultModelsType:
#         registry.global_types["models"] = {
#             "type": "object",
#             "additionalProperties": False,
#             "required": [],
#             "properties": {},
#         }
#
#     registry.global_types["models"] = {
#         **registry.global_types["models"],
#         "required": [*registry.global_types["models"]["required"], definition_name],
#         "properties": {
#             **registry.global_types["models"]["properties"],
#             definition_name: schema.schema,
#         },
#     }


_SingleSerializable = Union[
    None,
    str,
    bool,
    "FormType",
    "FormSetType",
    Dict[str, Union[str, int, float, bool, None]],
    django_forms.BaseForm,
    Sequence[
        Tuple[
            Union[
                Sequence[Tuple[Union[str, bool, int, None], ...]],
                str,
                bool,
                int,
                Dict[str, Union[str, int, float, bool, None]],
            ],
            ...,
        ]
    ],
    Tuple[
        Union[
            str,
            int,
            float,
            bool,
            Sequence[Tuple[Union[str, int, float, bool, "TypeHint", None], ...]],
            Mapping[str, Union[str, int, float, bool, Sequence[str], None]],
            "TypeHint",
        ],
        ...,
    ],
]

Serializable = Tuple[_SingleSerializable, ...]


K = TypeVar("K")
P = TypeVar("P", bound=Serializable)

View = Callable[[HttpRequest, K], Union[P, HttpResponse]]
NoArgsView = Callable[[HttpRequest], Union[P, HttpResponse]]


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def render_jsx(
    request: HttpRequest, template_name: str, props: Union[P, HttpResponse]
) -> HttpResponse:
    return HttpResponse("This needs to be migrated to render_jsx_to_string()")


@overload
def ssr(
    *, props: Type[P], params: None = None
) -> Callable[
    [NoArgsView[P]], Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse]
]: ...


@overload
def ssr(
    *, props: Type[P], params: Type[K]
) -> Callable[
    [View[K, P]], Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse]
]: ...


def ssr(*, props: Type[P], params: Optional[Type[K]] = None) -> Union[
    Callable[
        [NoArgsView[P]],
        Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse],
    ],
    Callable[
        [View[K, P]], Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse]
    ],
]:
    from .serialization.registry import type_registry

    type_registry[props.__name__] = props  # type: ignore[assignment]

    def no_args_wrap_with_jsx(
        original: NoArgsView[P],
    ) -> Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse]:
        def wrapper(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            props = original(request)
            template_name = to_camel_case(original.__name__)

            return render_jsx(request, template_name, props)

        return wrapper

    def wrap_with_jsx(
        original: View[K, P]
    ) -> Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse]:
        def wrapper(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            props = original(request, cast(Any, params)(**kwargs))
            template_name = to_camel_case(original.__name__)

            return render_jsx(request, template_name, props)

        return wrapper

    if params is None:
        return no_args_wrap_with_jsx
    else:
        return wrap_with_jsx


class TypeHint(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass


def create_schema(Type: Any, definitions: Dict[Any, Any], ref: bool = True) -> Any:
    if isinstance(Type, _GenericAlias):
        if Type.__origin__ == tuple:
            *tuple_args, last_arg = Type.__args__

            if last_arg is Ellipsis:
                return {
                    "type": "array",
                    "items": create_schema(tuple_args[0], definitions),
                }

            return {
                "type": "array",
                "items": [
                    create_schema(Subtype, definitions) for Subtype in Type.__args__
                ],
            }

    if (
        getattr(Type, "__origin__", None) == Union
        or str(Type.__class__) == "typing.Union"
    ):  # TODO: find a better way to do this.
        return {"anyOf": [create_schema(field, definitions) for field in Type.__args__]}
    elif str(Type.__class__) == "typing.Any":  # TODO: find a better way to do this.
        return {}
    elif Type == Any:  # TODO: find a better way to do this.
        return {}
    elif getattr(Type, "_name", None) == "Dict":
        return {
            "type": "object",
            "additionalProperties": create_schema(Type.__args__[1], definitions),
        }
    elif getattr(Type, "_name", None) == "List":
        return {"type": "array", "items": create_schema(Type.__args__[0], definitions)}
    elif issubclass(Type, List):
        return {"type": "array", "items": create_schema(Type.__args__[0], definitions)}
    elif issubclass(Type, Dict):
        return {
            "type": "object",
            "additionalProperties": create_schema(Type.__args__[1], definitions),
        }
    elif issubclass(Type, bool):
        return {"type": "boolean"}
    elif issubclass(Type, int):
        return {"type": "number"}
    elif issubclass(Type, str):
        return {"type": "string"}
    elif Type is type(None):  # noqa: E721
        return {"type": "null"}
    elif hasattr(Type, "_asdict"):
        definition_name = f"{Type.__module__}.{Type.__qualname__}"

        if ref is False or definition_name not in definitions:
            required = []
            properties = {}

            for field_name, SubType in Type.__annotations__.items():
                field_schema = create_schema(SubType, definitions, ref=ref)

                if field_schema is not None:
                    required.append(field_name)
                    properties[field_name] = field_schema

            definition = {
                # "title": Type.__name__,
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required,
            }

            if ref is False:
                return definition
            definitions[definition_name] = definition

        return {"$ref": f"#/$defs/{definition_name}"}
    elif issubclass(Type, django_forms.formsets.BaseFormSet):
        form_set_schema = create_schema(FormSetType, definitions, ref=False)
        form_schema = create_schema(Type.form, definitions)

        # We use our own management form because base_fields is set dynamically
        # by Django in django.forms.formsets.
        class ManagementForm(django_forms.formsets.ManagementForm):
            base_fields: Any  # type: ignore[misc]

        ManagementForm.base_fields = ManagementForm().base_fields

        management_form_schema = create_schema(ManagementForm, definitions)

        return {
            **form_set_schema,
            "properties": {
                **form_set_schema["properties"],
                "empty_form": form_schema,
                "forms": {"type": "array", "items": form_schema},
                "management_form": management_form_schema,
            },
        }

    elif issubclass(Type, django_forms.BaseForm):
        definition_name = f"{Type.__module__}.{Type.__qualname__}"
        required = []
        properties = {}
        error_properties = {}
        field_schema = create_schema(FieldType, definitions)

        # We manually build errors using type augmentation.
        error_schema = create_schema(FormError, definitions)

        for field_name, SubType in Type.base_fields.items():
            required.append(field_name)
            properties[field_name] = field_schema
            error_properties[field_name] = error_schema

        definitions["Form"] = {
            "title": "Form",
            "type": "object",
            "additionalProperties": False,
        }
        definitions[definition_name] = {
            "title": Type.__name__,
            "allOf": [
                {"$ref": "#/$defs/Form"},
                {
                    "type": "object",
                    "properties": {
                        "errors": {
                            "type": "object",
                            "properties": error_properties,
                            "additionalProperties": False,
                        },
                        "fields": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                            "additionalProperties": False,
                        },
                        "prefix": {"type": "string"},
                        "iterator": {
                            "type": "array",
                            "items": {"enum": required, "type": "string"},
                        },
                    },
                    "additionalProperties": False,
                    "required": ["prefix", "fields", "iterator", "errors"],
                },
            ],
        }

        return {"$ref": f"#/$defs/{definition_name}"}

    elif issubclass(Type, BasePickHolder):
        return Type.get_json_schema()
    elif issubclass(Type, TypeHint):
        return {"tsType": Type.name}
    assert False


class WidgetType(TypeHint):
    name = "WidgetType"


class FieldType(NamedTuple):
    name: str
    label: str
    help_text: str
    widget: WidgetType


FormError = Optional[List[str]]

FormErrors = Dict[str, FormError]


class FormType(NamedTuple):
    errors: Optional[FormErrors]
    fields: Dict[str, FieldType]
    iterator: List[str]
    prefix: str
    is_read_only: bool = False


class FormSetType(NamedTuple):
    initial: int
    total: int
    max_num: int
    min_num: int
    can_delete: bool
    can_order: bool
    non_form_errors: List[str]

    forms: List[FormType]
    empty_form: FormType
    management_form: FormType
    prefix: str


def describe_pattern(p):  # type: ignore[no-untyped-def]
    return str(p.pattern)


def extract_views_from_urlpatterns(  # type: ignore[no-untyped-def]
    urlpatterns, base="", namespace=None
):
    """
    Heavily modified version of the functiuon from django_extensions/management/commands/show_urls.py

    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a three-tuple: (view_func, regex, name, pattern)
    """
    views = []
    for p in urlpatterns:
        if isinstance(p, URLPattern):
            try:
                name: str | None
                if not p.name:
                    name = p.name
                elif namespace:
                    name = "{0}:{1}".format(namespace, p.name)
                else:
                    name = p.name
                pattern = describe_pattern(p)  # type: ignore[no-untyped-call]
                views.append((p.callback, base + pattern, name, p.pattern))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, URLResolver):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            if namespace and p.namespace:
                _namespace = "{0}:{1}".format(namespace, p.namespace)
            else:
                _namespace = p.namespace or namespace
            pattern = describe_pattern(p)  # type: ignore[no-untyped-call]

            if _namespace in getattr(
                settings, "REACTIVATED_IGNORED_URL_NAMESPACES", ["admin"]
            ):
                continue

            views.extend(
                extract_views_from_urlpatterns(  # type: ignore[no-untyped-call]
                    patterns, base + pattern, namespace=_namespace
                )
            )
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)
    return views
