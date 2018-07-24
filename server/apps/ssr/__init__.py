from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token

from typing import Any, Dict, Tuple, Union, Sequence, Mapping, TypeVar, Callable, Type, overload, Optional, cast, List

from mypy_extensions import TypedDict, Arg, KwArg

import abc
import simplejson


type_registry: Dict[str, Tuple] = {}


Serializable = Tuple[
    Union[
        str,
        bool,
        Dict[str, Union[str, int, float, bool, None]],
        Sequence[
            Tuple[
                Union[
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


class JSXResponse:
    def __init__(self, *, csrf_token: str, template_name: str, props: P) -> None:
        self.props = {
            'csrf_token': csrf_token,
            'template_name': template_name,
            **props._asdict(),  # type: ignore
        }

    def as_json(self) -> Any:
        return simplejson.dumps(self.props)


def render_jsx(request: HttpRequest, template_name: str, props: Union[P, HttpResponse]) -> HttpResponse:
    if isinstance(props, HttpResponse):
        return props

    response = JSXResponse(
        template_name=template_name,
        csrf_token=get_token(request),
        props=props,
    )
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


def create_schema(Type: Any) -> Any:
    if str(Type.__class__) == 'typing.Union':  # TODO: find a better way to do this.
        return {
            'anyOf': [
                create_schema(field) for field in Type.__args__
            ],
        }
    elif str(Type.__class__) == 'typing.Any':  # TODO: find a better way to do this.
        return {
        }
    elif issubclass(Type, List):
        return {
            'type': 'array',
            'items': create_schema(Type.__args__[0]),
        }
    elif issubclass(Type, Dict):
        return {
            'type': 'object',
            'additionalProperties': create_schema(Type.__args__[1]),
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
        return {
            'title': Type.__name__,
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                field_name: create_schema(SubType)
                for field_name, SubType in Type.__annotations__.items()
                if not issubclass(SubType, TypeHint)
            },
            'required': [
                field_name for field_name, SubType in Type.__annotations__.items()
            ],
        }
    elif issubclass(Type, TypeHint):
        """
            return {
                'title': Type().name,
                'type': 'object',
                'additionalProperties': False,
           }
        """
    assert False


def wrap_with_globals(props: Any) -> Any:
    return {
        **props,
        'properties': {
            **props['properties'],
            'template_name': {'type': 'string'},
            'csrf_token': {'type': 'string'},
        },
        'required': [
            *props['required'],
            'template_name',
            'csrf_token',
        ],
    }


def generate_schema() -> str:
    schema = {
        'title': 'Schema',
        'type': 'object',
        'properties': {
            name: wrap_with_globals(create_schema(Props))
            for name, Props in type_registry.items()
        },
        'additionalProperties': False,
        'required': [name for name in type_registry.keys()],
    }
    return simplejson.dumps(schema, indent=4)
