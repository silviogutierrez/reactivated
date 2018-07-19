from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect

from typing import Any, NamedTuple, Generic, TypeVar, Union, Dict, Optional, List, Any, Tuple, Sequence, Mapping, overload

from apps.testing import models

import abc
import simplejson


class Trinket(NamedTuple):
    name: str
    url: str


class TypeHint(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass


class WidgetType(TypeHint):
    name = 'WidgetType'


class FieldType(NamedTuple):
    name: str
    label: str
    widget: WidgetType


class FormType(NamedTuple):
    errors: Dict[str, Optional[List[str]]]
    fields: List[FieldType]


class FormViewProps(NamedTuple):
    widget_list: List[Trinket]
    form: FormType


T = TypeVar('T')


class JSXResponse:
    def __init__(self, *, csrf_token: str, template_name: str, props: T) -> None:
        self.props = {
            'csrf_token': csrf_token,
            'template_name': template_name,
            **props._asdict(),  # type: ignore
        }

    def as_json(self) -> Any:
        return simplejson.dumps(self.props)


def render_jsx(request: HttpRequest, template_name: str, props: T) -> HttpResponse:
    if isinstance(props, HttpResponse):
        return props

    response = JSXResponse(
        template_name=template_name,
        csrf_token=get_token(request),
        props=props,
    )
    return HttpResponse(response.as_json(), content_type='application/ssr+json')


class SSRFormRenderer:
    def render(self, template_name, context, request=None):
        return simplejson.dumps(context)


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


def schema(request: HttpRequest) -> HttpResponse:
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
    return HttpResponse(simplejson.dumps(schema), content_type='application/json')


def test_form(request: HttpRequest) -> HttpResponse:
    from django import forms
    from django.contrib.auth.models import User

    class TestForm(forms.Form):
        first_field = forms.CharField()
        single = forms.ChoiceField(
            required=True,
            choices=(
                (None, '----'),
                (1, 'M'),
                (2, 'F'),
            ),
        )
        flag = forms.ChoiceField(
            required=False,
            choices=(
                (False, 'No'),
                (True, 'Yes'),
            ),
        )
        multiple = forms.MultipleChoiceField(
            required=False,
            choices=(
                (1, 'Foo'),
                (2, 'Bar'),
            ),
        )
        model_single = forms.ModelChoiceField(
            required=False,
            queryset=User.objects.all(),
        )
        model_multiple = forms.ModelMultipleChoiceField(
            required=False,
            queryset=User.objects.all(),
        )

    if request.method == 'POST':
        form = TestForm(request.POST, renderer=SSRFormRenderer())

        if form.is_valid():
            return redirect(request.path)  # type: ignore
    else:
        form = TestForm(renderer=SSRFormRenderer())

    serialized_form = {
        'errors': form.errors,
        'fields': [simplejson.loads(str(field)) for field in form],
    }
    base_form = TestForm()
    # assert False

    response = JSXResponse(
        template_name='FormView',
        csrf_token=get_token(request),
        props={
            'form': serialized_form,
        },
    )
    return HttpResponse(simplejson.dumps(response), content_type='application/ssr+json')


type_registry: Dict[str, NamedTuple] = {}


class TrinketListProps(NamedTuple):
    trinket_list: List[Trinket]



from typing import Callable, Tuple, Type, cast
from mypy_extensions import TypedDict, Arg, KwArg


class EmptyParams(NamedTuple):
    pass


class TrinketListParams(NamedTuple):
    pass


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

View = Callable[[HttpRequest, K], P]
NoArgsView = Callable[[HttpRequest], P]


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


    reveal_type(form_view)


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


@ssr(props=TrinketListProps, params=TrinketListParams)
def trinket_list(request: HttpRequest, params: TrinketListParams) -> TrinketListProps:
    trinket_list = [
        Trinket(
            name=trinket.name,
            url=f'/trinkets/{trinket.pk}/',
        ) for trinket in models.Trinket.objects.all()
    ]

    return TrinketListProps(
        trinket_list=trinket_list,
    )


class TrinketDetailParams(NamedTuple):
    pk: int


class TrinketDetailProps(NamedTuple):
    trinket: Trinket
    back_url: str


class NestedNewThing(NamedTuple):
    b: bool
    f: int


class NewThing(NamedTuple):
    a: str
    b: bool
    c: NestedNewThing


@ssr(props=TrinketDetailProps, params=TrinketDetailParams)
def trinket_detail(request: HttpRequest, params: TrinketDetailParams) -> TrinketDetailProps:
    trinket = models.Trinket.objects.get(pk=params.pk)

    return TrinketDetailProps(
        trinket=Trinket(
            name=trinket.name,
            url=f'/trinkets/{trinket.pk}/',
        ),
        back_url='/trinkets/',
    )


@ssr(props=NewThing, params=TrinketListParams)
def my_thang(request: HttpRequest, params: TrinketListParams) -> NewThing:
    return NewThing(
        a='a',
        b=True,
        c=NestedNewThing(
            b=True,
            f=5,
        ),
    )


def do_something(thing: Serializable) -> None:
    pass


@ssr(props=FormViewProps)
def form_view(request: HttpRequest) -> FormViewProps:
    from django import forms

    class TrinketForm(forms.ModelForm):
        class Meta:
            model = models.Trinket
            fields = '__all__'

    if request.method == 'POST':
        form = TrinketForm(request.POST, renderer=SSRFormRenderer())

        if form.is_valid():
            form.save()
            return redirect(request.path)  # type: ignore
    else:
        form = TrinketForm(renderer=SSRFormRenderer())

    serialized_form = FormType(
        errors=form.errors,
        fields=[
            FieldType(
                widget=simplejson.loads(str(field))['widget'],
                name=field.name,
                label=field.label,
            ) for field in form
        ],
   )

    return FormViewProps(
        form=serialized_form,
        widget_list=[
            Trinket(
                name=trinket.name,
                url=f'/trinkets/{trinket.pk}/',
            ) for trinket in models.Trinket.objects.all()
        ],
    )
