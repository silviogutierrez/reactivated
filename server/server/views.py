from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect

from typing import Any, NamedTuple, Generic, TypeVar, Union, Dict, Optional, List, Any

from server.testing import models

import simplejson


class Widget(NamedTuple):
    name: str
    url: str


class FieldType(NamedTuple):
    name: str
    label: str
    widget: Any


class FormType(NamedTuple):
    errors: Dict[str, Optional[List[str]]]
    fields: List[FieldType]


class FormViewProps(NamedTuple):
    widget_list: List[Widget]
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
            },
            'required': [
                field_name for field_name, SubType in Type.__annotations__.items()
            ],
        }
    assert False


def schema(request: HttpRequest) -> HttpResponse:
    Type = Widget

    schema = create_schema(FormViewProps)
    return HttpResponse(simplejson.dumps(schema), content_type='application/json')

    def python_type_to_json_schema_type(python_type: Any) -> str:
        if python_type == str:
            return 'string'
        elif python_type == int:
            return 'number'
        assert False, "Can't happen."

    schema = {
        'title': Type.__name__,
        'type': 'object',
        'properties': {
            field_name: {
                'type': python_type_to_json_schema_type(field),
            } for field_name, field in Type.__annotations__.items()
        },
        'required': [
            field_name for field_name, field in Type.__annotations__.items()
        ],
        'additionalProperties': False,
    }
    return HttpResponse(simplejson.dumps(schema), content_type='application/json')

def test_record(request: HttpRequest) -> HttpResponse:
    from django import forms

    class WidgetForm(forms.ModelForm):
        class Meta:
            model = models.Widget
            fields = '__all__'

    if request.method == 'POST':
        form = WidgetForm(request.POST, renderer=SSRFormRenderer())

        if form.is_valid():
            form.save()
            return redirect(request.path)
    else:
        form = WidgetForm(renderer=SSRFormRenderer())

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

    props = FormViewProps(
        form=serialized_form,
        widget_list=[
            Widget(
                name=widget.name,
                url='foo',
            ) for widget in models.Widget.objects.all()
        ],
    )

    return render_jsx(request, 'FormView', props)


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
            return redirect(request.path)
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
