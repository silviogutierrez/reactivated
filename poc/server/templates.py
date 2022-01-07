from typing import NamedTuple

from reactivated import template

from . import forms


@template
class HelloWorld(NamedTuple):
    pass


@template
class Storyboard(NamedTuple):
    form: forms.StoryboardForm
