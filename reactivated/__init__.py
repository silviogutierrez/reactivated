import abc
import inspect
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from django import forms as django_forms
from django.core.exceptions import ViewDoesNotExist
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, URLResolver
from django.utils import autoreload
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

original_restart_with_reloader = autoreload.restart_with_reloader


def patched_restart_with_reloader() -> None:
    from . import processes
    from .apps import generate_schema, get_schema

    schema = get_schema()
    generate_schema(schema)
    processes.start_tsc()
    processes.start_client()
    processes.start_renderer()
    original_restart_with_reloader()

    # Start the renderer and attach it to an env variable
    # Then for production builds, the renderer is started in apps if not already started in the env variable.
    # No need to lazy load I think.


autoreload.restart_with_reloader = patched_restart_with_reloader  # type: ignore[assignment]


def export(var: Any) -> None:
    """See: https://stackoverflow.com/a/18425523"""
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()  # type: ignore[union-attr]
    name = [var_name for var_name, var_val in callers_local_vars if var_val is var][0]
    # var.__reactivated_serialize_as_is = True

    registry.value_registry.update({name: (var, True)})


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
]:
    ...


@overload
def ssr(
    *, props: Type[P], params: Type[K]
) -> Callable[
    [View[K, P]], Callable[[Arg(HttpRequest, "request"), KwArg(Any)], HttpResponse]
]:
    ...


def ssr(
    *, props: Type[P], params: Optional[Type[K]] = None
) -> Union[
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

        return {"$ref": f"#/definitions/{definition_name}"}
    elif issubclass(Type, django_forms.formsets.BaseFormSet):
        form_set_schema = create_schema(FormSetType, definitions, ref=False)
        form_schema = create_schema(Type.form, definitions)

        # We use our own management form because base_fields is set dynamically
        # by Django in django.forms.formsets.
        class ManagementForm(django_forms.formsets.ManagementForm):
            base_fields: Any

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
                {"$ref": "#/definitions/Form"},
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

        return {"$ref": f"#/definitions/{definition_name}"}

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
            views.extend(
                extract_views_from_urlpatterns(  # type: ignore[no-untyped-call]
                    patterns, base + pattern, namespace=_namespace
                )
            )
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)
    return views
