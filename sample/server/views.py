from django.http import HttpRequest
from django.template.response import TemplateResponse

from . import forms


def hello_world(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "hello_world.tsx", {})


def sample_form(request: HttpRequest) -> TemplateResponse:
    form = forms.SampleForm()
    return TemplateResponse(request, "sample_form.tsx", {"form": form})
