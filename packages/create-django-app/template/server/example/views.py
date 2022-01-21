from django.http import (
    HttpRequest,
    HttpResponse,
)

from . import templates


def django_default(request: HttpRequest,) -> HttpResponse:
    return templates.DjangoDefault(version="X").render(request)
