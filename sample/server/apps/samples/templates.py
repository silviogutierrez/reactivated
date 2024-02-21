from typing import NamedTuple, Literal

from reactivated import Pick, template

from . import forms, models

Opera = Pick[models.Opera, Literal["name", "composer.name", "style"]]


@template
class HelloWorld(NamedTuple):
    opera: Opera


@template
class Storyboard(NamedTuple):
    form: forms.StoryboardForm
