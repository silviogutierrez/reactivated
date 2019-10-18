from django.http import HttpRequest, JsonResponse
from django.template.response import TemplateResponse

from . import forms
import simplejson

from reactivated.apps import get_schema


def hello_world(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "hello_world.tsx", {})


def sample_form(request: HttpRequest) -> TemplateResponse:
    form = forms.SampleForm()


def schema(request: HttpRequest) -> TemplateResponse:
    return JsonResponse(simplejson.loads(get_schema()))
