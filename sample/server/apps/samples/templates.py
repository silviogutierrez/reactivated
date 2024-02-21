from typing import NamedTuple

from reactivated import template, Pick

from . import forms, models


Opera = Pick(models.Opera, fields=["name", "composer.name", "style"])


@template
class HelloWorld(NamedTuple):
    opera: Opera


@template
class Storyboard(NamedTuple):
    form: forms.StoryboardForm
