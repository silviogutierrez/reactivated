from typing import NamedTuple

from reactivated import Pick, template

from . import forms, models


@template
class HelloWorld(NamedTuple):
    opera: Pick[models.Opera, "name", "composer.name", "style"]


@template
class Storyboard(NamedTuple):
    form: forms.StoryboardForm
