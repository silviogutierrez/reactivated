from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.template.defaultfilters import escape

from typing import Any, Dict, Tuple, Union, Sequence, Mapping, TypeVar, Callable, Type, overload, Optional, cast, List, NamedTuple

from mypy_extensions import TypedDict, Arg, KwArg

import abc
import datetime
import simplejson


type_registry: Dict[str, Tuple] = {}


Serializable = Tuple[
    Union[
        None,
        str,
        bool,
        Dict[str, Union[str, int, float, bool, None]],
        forms.BaseForm,
        Sequence[
            Tuple[
                Union[
                    Sequence[
                        Tuple[
                            Union[
                                str,
                                bool,
                                int,
                                None,
                            ],
                            ...
                        ],
                    ],
                    str,
                    bool,
                    int,
                    Dict[str, Union[str, int, float, bool, None]],
                ],
                ...
            ]
        ],

        Tuple[
            Union[
                str,
                int,
                float,
                bool,

                Sequence[
                    Tuple[
                        Union[
                            str,
                            int,
                            float,
                            bool,
                            'TypeHint',
                            None,
                        ],
                        ...
                    ]
                ],

                Mapping[str, Union[
                    str,
                    int,
                    float,
                    bool,
                    Sequence[str],
                    None
                ]],
                'TypeHint',
            ],
            ...
        ]
    ],
    ...
]


K = TypeVar('K')
P = TypeVar('P', bound=Serializable)

View = Callable[[HttpRequest, K], Union[P, HttpResponse]]
NoArgsView = Callable[[HttpRequest], Union[P, HttpResponse]]


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


    reveal_type(form_view)


class Message(NamedTuple):
    level: int
    level_tag: str
    message: str


class Request(NamedTuple):
    path: str


class Context(NamedTuple):
    template_name: str
    csrf_token: str
    request: Request
    messages: List[Message]


def encode_complex_types(obj: Any) -> Serializable:
    """
    Handles dates, forms, and other types.
    From: https://stackoverflow.com/a/22238613
    """
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif isinstance(obj, forms.BaseForm):
        return serialize_form(obj)

    raise TypeError("Type %s not serializable" % type(obj))


class JSXResponse:
    def __init__(self, *, context: Context, props: P) -> None:

        self.data = {
            'context': context._asdict(),
            'props': props if isinstance(props, dict) else props._asdict(),  # type: ignore
        }

    def as_json(self) -> Any:
        return simplejson.dumps(self.data, default=encode_complex_types)  #, use_decimal=False)


def render_jsx(request: HttpRequest, template_name: str, props: Union[P, HttpResponse]) -> HttpResponse:
    if isinstance(props, HttpResponse):
        return props


    current_messages = messages.get_messages(request)

    response = JSXResponse(
        context=Context(
            request=Request(
                path=request.path,
            ),
            template_name=template_name,
            csrf_token=get_token(request),
            messages=[
                Message(
                    level=m.level,
                    level_tag=m.level_tag,
                    message=m.message,
                ) for m in current_messages
            ],
        ),
        props=props,
    )

    if 'debug' in request.GET:
        return HttpResponse('<html><body><h1>Debug response</h1><pre>' + escape(response.as_json()) + '</pre></body></html>', content_type='text/html')

    return HttpResponse(response.as_json(), content_type='application/ssr+json')


@overload
def ssr(*,
        props: Type[P],
        params: None = None) -> Callable[[NoArgsView[P]], Callable[[Arg(HttpRequest, 'request'), KwArg(Any)], HttpResponse]]: ...


@overload
def ssr(*,
        props: Type[P],
        params: Type[K]) -> Callable[[View[K, P]], Callable[[Arg(HttpRequest, 'request'), KwArg(Any)], HttpResponse]]: ...


def ssr(*,
        props: Type[P],
        params: Optional[Type[K]] = None) -> Union[
                                                 Callable[[NoArgsView[P]], Callable[[Arg(HttpRequest, 'request'), KwArg(Any)], HttpResponse]],
                                                 Callable[[View[K, P]], Callable[[Arg(HttpRequest, 'request'), KwArg(Any)], HttpResponse]],
                                             ]:
    type_registry[props.__name__] = props  # type: ignore

    def no_args_wrap_with_jsx(original: NoArgsView[P]) -> Callable[[Arg(HttpRequest, 'request'), KwArg(Any)], HttpResponse]:
        def wrapper(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            props = original(request)
            template_name = to_camel_case(original.__name__)

            return render_jsx(request, template_name, props)

        return wrapper

    def wrap_with_jsx(original: View[K, P]) -> Callable[[Arg(HttpRequest, 'request'), KwArg(Any)], HttpResponse]:
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


def create_schema(Type: Any, definitions: Dict, ref: bool = True) -> Any:
    if (getattr(Type, '__origin__', None) == Union or
        str(Type.__class__) == 'typing.Union'):  # TODO: find a better way to do this.
        return {
            'anyOf': [
                create_schema(field, definitions) for field in Type.__args__
            ],
        }
    elif str(Type.__class__) == 'typing.Any':  # TODO: find a better way to do this.
        return {
        }
    elif getattr(Type, '_name', None) == 'Dict':
        return {
            'type': 'object',
            'additionalProperties': create_schema(Type.__args__[1], definitions),
        }
    elif getattr(Type, '_name', None) == 'List':
        return {
            'type': 'array',
            'items': create_schema(Type.__args__[0], definitions),
        }
    elif issubclass(Type, List):
        return {
            'type': 'array',
            'items': create_schema(Type.__args__[0], definitions),
        }
    elif issubclass(Type, Dict):
        return {
            'type': 'object',
            'additionalProperties': create_schema(Type.__args__[1], definitions),
        }
    elif issubclass(Type, bool):
        return {
            'type': 'bool',
        }
    elif issubclass(Type, int):
        return {
            'type': 'number',
        }
    elif issubclass(Type, str):
        return {
            'type': 'string',
        }
    elif Type is type(None):
        return {
            'type': 'null',
        }
    elif hasattr(Type, '_asdict'):
        definition_name = f'{Type.__module__}.{Type.__qualname__}'

        if ref is False or definition_name not in definitions:
            required = []
            properties = {}

            for field_name, SubType in Type.__annotations__.items():
                field_schema = create_schema(SubType, definitions)

                if field_schema is not None:

                    required.append(field_name)
                    properties[field_name] = field_schema

            definition = {
                'title': Type.__name__,
                'type': 'object',
                'additionalProperties': False,
                'properties': properties,
                'required': required,
            }

            if ref is False:
                return definition
            definitions[definition_name] = definition

        return {
            '$ref': f'#/definitions/{definition_name}',
        }
    elif issubclass(Type, forms.BaseForm):
        definition_name = f'{Type.__module__}.{Type.__qualname__}'
        required = []
        properties = {}
        field_schema = create_schema(FieldType, definitions)
        # We manually build errors using type augmentation.
        # error_schema = create_schema(FormErrors, definitions)

        for field_name, SubType in Type.base_fields.items():
            required.append(field_name)
            properties[field_name] = field_schema

        definitions['Form'] = {
            'title': 'Form',
            'type': 'object',
            'additionalProperties': False,
        }
        definitions[definition_name] = {
            'title': Type.__name__,
            'allOf': [
                {
                    '$ref': '#/definitions/Form',
                },
                {
                    'type': 'object',
                    'properties': {
                        # 'errors': error_schema,
                        'fields': {
                            'type': 'object',
                            'properties': properties,
                            'required': required,
                            'additionalProperties': False,
                        },
                    },
                    'additionalProperties': False,
                    'required': [
                        'fields',
                        # 'errors',
                    ],
                },
            ],
        }

        return {
            '$ref': f'#/definitions/{definition_name}',
        }

    elif issubclass(Type, TypeHint):
        return None
        """
            return {
                'title': Type().name,
                'type': 'object',
                'additionalProperties': False,
           }
        """
    assert False


"""
def wrap_with_globals(props: Any, definitions: Dict) -> Any:
    message_schema = create_schema(Message, definitions)

    return {
        **props,
        'properties': {
            **props['properties'],
            'template_name': {'type': 'string'},
            'csrf_token': {'type': 'string'},
            'messages': {
                'type': 'array',
                'items': message_schema,
            },
        },
        'required': [
            *props['required'],
            'template_name',
            'csrf_token',
            'messages',
        ],
    }
"""


def generate_schema() -> str:
    definitions = {}

    schema = {
        'title': 'Schema',
        'type': 'object',
        'definitions': definitions,
        'properties': {
            # name: wrap_with_globals(create_schema(Props, definitions, ref=False), definitions)
            name: create_schema(Props, definitions, ref=False)
            for name, Props in type_registry.items()
        },
        'additionalProperties': False,
        'required': [name for name in type_registry.keys()],
    }

    return simplejson.dumps(schema, indent=4)


class WidgetType(TypeHint):
    name = 'WidgetType'


class FieldType(NamedTuple):
    name: str
    label: str
    help_text: str
    widget: WidgetType


FormErrors = Dict[str, Optional[List[str]]]


class FormType(NamedTuple):
    errors: FormErrors
    fields: Dict[str, FieldType]
    iterator: List[str]


class SSRFormRenderer:
    def render(self, template_name, context, request=None):
        return simplejson.dumps(context)


def serialize_form(form: Optional[forms.BaseForm]) -> Optional[FormType]:
    if form is None:
        return None

    form.renderer = SSRFormRenderer()
    fields = {
        field.name: FieldType(
            widget=simplejson.loads(str(field))['widget'],
            name=field.name,
            label=str(field.label), # This can be a lazy proxy, so we must call str on it.
            help_text=str(field.help_text), # This can be a lazy proxy, so we must call str on it.
        ) for field in form
    }

    return FormType(
        errors=form.errors,
        fields=fields,
        iterator=list(fields.keys()),
   )


def generate_settings() -> None:
    settings_to_serialize = {
        setting_name: setting_value
        for setting_name, setting_value in settings._wrapped.__dict__.items() if setting_name not in ['_explicit_settings']
    }
    return simplejson.dumps(settings_to_serialize, indent=4)
