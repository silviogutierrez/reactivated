from reactivated import template

from typing import NamedTuple

from django import forms


class Foo(forms.Form):
    pass


@template
class DjangoDefault(NamedTuple):
    version: str
    form: Foo
