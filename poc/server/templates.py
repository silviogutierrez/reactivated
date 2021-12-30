from typing import NamedTuple

from reactivated import Pick, template

from . import forms


@template
class HelloWorld(NamedTuple):
    pass


@template
class Storyboard(NamedTuple):
    form: forms.StoryboardForm
