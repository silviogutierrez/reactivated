import simplejson
from django.http import HttpRequest, JsonResponse
from django.template.response import TemplateResponse

from reactivated.apps import get_schema

from . import forms


def hello_world(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "hello_world.tsx", {})


def sample_form(request: HttpRequest) -> TemplateResponse:
    form = forms.SampleForm()
    return TemplateResponse(request, "sample_form.tsx", {"form": form})


def schema(request: HttpRequest) -> JsonResponse:
    return JsonResponse(simplejson.loads(get_schema()))
