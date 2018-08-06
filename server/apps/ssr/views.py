from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect

from typing import Any, NamedTuple, Generic, TypeVar, Union, Dict, Optional, List, Any, Tuple, Sequence, Mapping, overload

# from server.apps.testing import models

from . import ssr, generate_schema, TypeHint, FormType

import abc
import simplejson


class Trinket(NamedTuple):
    name: str
    url: str


class FormViewProps(NamedTuple):
    widget_list: List[Trinket]
    form: FormType



class SSRFormRenderer:
    def render(self, template_name, context, request=None):
        return simplejson.dumps(context)


def schema(request: HttpRequest) -> HttpResponse:
    return HttpResponse(generate_schema(), content_type='application/json')



type_registry: Dict[str, NamedTuple] = {}


class TrinketListProps(NamedTuple):
    trinket_list: List[Trinket]



from typing import Callable, Tuple, Type, cast
from mypy_extensions import TypedDict, Arg, KwArg


class EmptyParams(NamedTuple):
    pass


class TrinketListParams(NamedTuple):
    pass


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


@ssr(props=FormViewProps)
def form_view(request: HttpRequest) -> Union[FormViewProps, HttpResponse]:
    from django import forms

    class TrinketForm(forms.ModelForm):
        class Meta:
            model = models.Trinket
            fields = '__all__'

    if request.method == 'POST':
        form = TrinketForm(request.POST, renderer=SSRFormRenderer())

        if form.is_valid():
            form.save()
            return redirect(request.path)
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
