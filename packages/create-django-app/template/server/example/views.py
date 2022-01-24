from django.http import (
    HttpRequest,
    HttpResponse,
)

from . import templates
from django.utils.version import get_docs_version


def django_default(request: HttpRequest,) -> HttpResponse:
    return templates.DjangoDefault(version=get_docs_version()).render(request)
