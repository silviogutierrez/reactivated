from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from typing import Any, NamedTuple

import simplejson


class JSXResponse(NamedTuple):
    template_name: str
    props: Any


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


def test_form(request: HttpRequest) -> HttpResponse:
    from django import forms
    from django.contrib.auth.models import User

    class TestForm(forms.Form):
        first_field = forms.CharField()
        single = forms.ChoiceField(
            required=False,
            choices=(
                (None, '----'),
                (1, 'M'),
                (2, 'F'),
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

    form = TestForm(request.GET, renderer=SSRFormRenderer())
    serialized_form = [
        simplejson.loads(str(field)) for field in form
    ]

    response = JSXResponse(
        template_name='FormView',
        props={
            'form': serialized_form,
        },
    )
    return HttpResponse(simplejson.dumps(response), content_type='application/x.ssr')
