from typing import List, NamedTuple

from reactivated import Pick, template

from . import forms, models


@template
class TypedTemplate(NamedTuple):
    opera: Pick[models.Opera, "name", "composer.name", "has_piano_transcription"]
    composer: Pick[
        models.Composer,
        "name",
        "countries.name",
        "countries.id",
        "countries.continent.name",
        "countries.continent.hemisphere",
        "countries.continent.countries.name",
    ]
    all_operas: List[Pick[models.Opera, "name"]]


@template
class DataBrowser(NamedTuple):
    composer_form_set: forms.ComposerFormSet
    composer_form: forms.ComposerForm
    opera_form_set: forms.OperaFormSet
    opera_form: forms.OperaForm


@template
class AjaxPlayground(NamedTuple):
    pass


@template
class FormPlayground(NamedTuple):
    form: forms.PlaygroundForm
