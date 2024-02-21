from typing import NamedTuple

from reactivated import template

from . import forms, models

Opera = models.Opera  # Pick[models.Opera, "name", "composer.name", "style"]


@template
class HelloWorld(NamedTuple):
    opera: Opera


@template
class Storyboard(NamedTuple):
    form: forms.StoryboardForm
