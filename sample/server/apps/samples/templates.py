from typing import Annotated

from reactivated import Template, pick
from reactivated.forms import DjangoForm, DjangoFormSet

from . import forms, models

Opera = pick(models.Opera, fields=["name", "composer.name", "style"])


class HelloWorld(Template):
    opera: Opera.output


class Storyboard(Template):
    form: Annotated[forms.StoryboardForm, DjangoForm]
    form_set: Annotated[forms.OperaFormSet, DjangoFormSet]
