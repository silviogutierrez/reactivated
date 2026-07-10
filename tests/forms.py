import pytest
from django import forms as django_forms

from reactivated.forms import schema as serialization
from sample.server.apps.samples import forms, models


class ComposerForm(django_forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = ["name"]


ComposerFormSet = django_forms.formset_factory(ComposerForm)


@pytest.mark.django_db
def test_form_class_not_instance(snapshot):
    generated_schema = serialization.create_schema(forms.OperaForm, {})
    serialized = serialization.serialize(forms.OperaForm, generated_schema)
    assert generated_schema == snapshot
    assert serialized == snapshot


@pytest.mark.django_db
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
