from django.http import HttpRequest, HttpResponse

from . import templates


def home_page(request: HttpRequest) -> HttpResponse:
    return templates.HomePage().render(request)
