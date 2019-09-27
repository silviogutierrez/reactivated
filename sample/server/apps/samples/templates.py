from typing import NamedTuple

from reactivated import Pick, template

from . import forms, models


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


@template
class DataBrowser(NamedTuple):
    composer_form_set: forms.ComposerFormSet  # type: ignore
    composer_form: forms.ComposerForm
    opera_form_set: forms.OperaFormSet  # type: ignore
    opera_form: forms.OperaForm
