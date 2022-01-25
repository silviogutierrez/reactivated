from typing import NamedTuple


from reactivated import template

from . import forms


@template
class DjangoDefault(NamedTuple):
    version: str
    form: forms.StoryboardForm
