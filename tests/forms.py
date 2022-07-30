import pytest
from django import forms as django_forms

from reactivated.forms import FormGroup
from sample.server.apps.samples import forms, models


class ComposerForm(django_forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = ["name"]


class OperaFormGroup(FormGroup):
    opera: forms.OperaForm
    composer: ComposerForm


@pytest.mark.django_db
def test_form_group():
    opera_form = forms.OperaForm({})
    composer_form = ComposerForm({})
    form_group = OperaFormGroup({})

    assert form_group.is_valid() is False
    assert form_group.errors["opera"] == opera_form.errors
    assert form_group.errors["composer"] == composer_form.errors

    composer = models.Composer.objects.create(name="Richard Wagner")

    form_group = OperaFormGroup(
        {
            "opera-name": "test",
            "opera-composer": composer.id,
            "opera-style": models.Opera.Style.GRAND,
            "composer-name": "John",
        }
    )
    assert form_group.is_valid() is True
