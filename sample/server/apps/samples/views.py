from django.http import (
    HttpRequest,
    HttpResponse,
)

from . import forms, models, templates


def hello_world(request: HttpRequest) -> HttpResponse:
    composer = models.Composer(name="Arrigo Boito")
    opera = models.Opera(name="Mefistofele", composer=composer)
    return templates.HelloWorld(opera=opera).render(request)
