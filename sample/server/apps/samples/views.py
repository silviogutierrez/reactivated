from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from reactivated.pick import new_pick, NoWay

from typing import NamedTuple

from . import forms, interfaces, models, templates
from typing import List, Type

Point = NamedTuple("Point", [("x", int)])


Blah = new_pick(models.Composer, ["name"])


# For some reason, new_pick is not valid as a type. We need to fix this.
class Thing:
    invalid_blah: Blah
    blah: List[Type[NoWay]]
    point: Point


def hello_world(request: HttpRequest) -> HttpResponse:
    reveal_type(NoWay)
    reveal_type(Blah)
    blah = Blah()
    blah.member_thing
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
