from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from . import forms, templates


def hello_world(request: HttpRequest) -> HttpResponse:
    return templates.HelloWorld().render(request)


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
    return templates.Storyboard(form=form,).render(request)
