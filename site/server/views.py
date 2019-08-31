from django.template.response import TemplateResponse

from django.http import HttpRequest, HttpResponse


def hello_world(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Ok")
