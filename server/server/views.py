from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect

from typing import Any, NamedTuple

from server.testing import models

import simplejson


class JSXResponse:
    def __init__(self, *, csrf_token: str, template_name: str, props: Any) -> None:
        self.props = {
            'csrf_token': csrf_token,
            'template_name': template_name,
            **props,
        }

    def as_json(self) -> Any:
        return simplejson.dumps(self.props)


def test(request: HttpRequest) -> HttpResponse:
    content = simplejson.dumps(JSXResponse(
        template_name='DetailView',
        props={
            'thing': 'bar',
        },
    ))
    return HttpResponse(content, content_type='application/json')


class SSRFormRenderer:
    def render(self, template_name, context, request=None):
        return simplejson.dumps(context)


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

    serialized_form = {
        'errors': form.errors,
        'fields': [
            {
                **simplejson.loads(str(field)),
                'name': field.name,
                'label': field.label,
            } for field in form
        ],
    }

    response = JSXResponse(
        template_name='FormView',
        csrf_token=get_token(request),
        props={
            'form': serialized_form,
            'widget_list': [
                widget.name for widget in models.Widget.objects.all()
            ],
        },
    )
    return HttpResponse(response.as_json(), content_type='application/ssr+json')


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
