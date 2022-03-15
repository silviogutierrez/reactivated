from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from . import forms, interfaces, models, templates


def hello_world(request: HttpRequest) -> HttpResponse:
    composer = models.Composer(name="Arrigo Boito")
    opera = models.Opera(
        name="Mefistofele", composer=composer, style=models.Opera.Style.GRAND
    )
    return templates.HelloWorld(opera=opera).render(request)


def storyboard(request: HttpRequest) -> HttpResponse:
    form = forms.StoryboardForm(
        request.POST or None,
        initial={
            "char_field": "Ok",
            "integer_field": 7,
            "date_field": timezone.localdate(),
            "date_time_field": timezone.now(),
            "enum_field": models.Opera.Style.VERISMO,
            "boolean_field": True,
        },
    )
    return templates.Storyboard(
        form=form,
    ).render(request)


def opera_list(request: HttpRequest) -> HttpResponse:
    operas = models.Opera.objects.all()

    return interfaces.OperaList(operas=list(operas)).render(request)
