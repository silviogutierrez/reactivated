from django.template.response import TemplateResponse

from django.http import HttpRequest


def hello_world(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "hello_world.tsx", {})
