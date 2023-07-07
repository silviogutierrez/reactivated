import pytest
from django import forms as django_forms

from reactivated import serialization
from reactivated.forms import FormGroup
from sample.server.apps.samples import forms, models

from .serialization import convert_to_json_and_validate


class ComposerForm(django_forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = ["name"]


ComposerFormSet = django_forms.formset_factory(ComposerForm)


class OperaFormGroup(FormGroup):
    opera: forms.OperaForm
    composer: ComposerForm
    composers: ComposerFormSet


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
            "composers-0-name": "John",
            "composers-INITIAL_FORMS": 1,
            "composers-TOTAL_FORMS": 1,
        }
    )
    assert form_group.is_valid() is True


@pytest.mark.django_db
def test_form_group_instance(snapshot):
    generated_schema = serialization.create_schema(OperaFormGroup, {})
    serialized = serialization.serialize(OperaFormGroup(), generated_schema)
    convert_to_json_and_validate(serialized, generated_schema)
    assert generated_schema == snapshot
    assert serialized == snapshot


def test_form_group_class_not_instance(snapshot):
    generated_schema = serialization.create_schema(OperaFormGroup, {})
    serialized = serialization.serialize(OperaFormGroup, generated_schema)
    convert_to_json_and_validate(serialized, generated_schema)
    assert generated_schema == snapshot
    assert serialized == snapshot


def test_form_class_not_instance(snapshot):
    generated_schema = serialization.create_schema(forms.OperaForm, {})
    serialized = serialization.serialize(forms.OperaForm, generated_schema)
    assert generated_schema == snapshot
    assert serialized == snapshot


def test_form_set_class_not_instance(snapshot):
    generated_schema = serialization.create_schema(forms.OperaFormSet, {})
    serialized = serialization.serialize(forms.OperaFormSet, generated_schema)
    assert generated_schema == snapshot
    assert serialized == snapshot


class FormWithModel(django_forms.Form):
    model_choice = django_forms.ModelChoiceField(queryset=models.Opera.objects.all())


def test_model_choice_fields_without_db_access_failure(snapshot):
    generated_schema = serialization.create_schema(FormWithModel, {})
    with pytest.raises(BaseException, match="Database access not allowed"):
        serialization.serialize(FormWithModel, generated_schema)


def test_model_choice_fields_without_db_access_passing(snapshot):
    generated_schema = serialization.create_schema(FormWithModel, {})
    generated_schema.definitions["is_static_context"] = True
    serialization.serialize(FormWithModel, generated_schema)
