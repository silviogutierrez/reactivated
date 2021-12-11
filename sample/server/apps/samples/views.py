from django.http import HttpRequest, HttpResponse

from . import models, templates


def hello_world(request: HttpRequest) -> HttpResponse:
    composer = models.Composer(name="Arrigo Boito")
    opera = models.Opera(
        name="Mefistofele", composer=composer, style=models.Opera.Style.GRAND
    )
    return templates.HelloWorld(opera=opera).render(request)
