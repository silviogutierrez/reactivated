from typing import List, NamedTuple

import pytest

from reactivated import Pick
from reactivated.serialization import create_schema, serialize
from sample.server.apps.samples import forms, models


class Spam(NamedTuple):
    thing: List[str]
    again: str


class Bar(NamedTuple):
    a: str
    b: bool


class Foo(NamedTuple):
    bar: Bar
    spam: Spam
    pick: Pick[models.Composer, "name", "operas.name"]


@pytest.mark.django_db
def test_serialization():
    composer = models.Composer.objects.create(name="Wagner")
    opera = models.Opera.objects.create(name="Götterdämmerung", composer=composer)

    instance = Foo(
        bar=Bar(a="a", b=True),
        spam=Spam(thing=["one", "two", "three", "four"], again="ok"),
        pick=composer,
    )
    definitions = {}
    generated_schema = create_schema(Foo, definitions)

    assert serialize(instance, generated_schema) == {
        "bar": {"a": "a", "b": True},
        "spam": {"thing": ["one", "two", "three", "four"], "again": "ok"},
        "pick": {"name": composer.name, "operas": [{"name": opera.name}]},
    }


def test_form():
    generated_schema = create_schema(forms.OperaForm, {})
    form = forms.OperaForm()
    serialized_form = serialize(form, generated_schema)

    form_with_errors = forms.OperaForm({})
    form_with_errors.is_valid()
    serialized_form = serialize(form_with_errors, generated_schema)
    assert "name" in serialized_form.errors


@pytest.mark.django_db
def test_form_set():
    generated_schema = create_schema(forms.OperaFormSet, {})
    form_set = forms.OperaFormSet()
    serialized_form_set = serialize(form_set, generated_schema)

    form_set_with_errors = forms.OperaFormSet({
        "form-TOTAL_FORMS": 20,
        "form-INITIAL_FORMS": 0,
    })
    form_set_with_errors.is_valid()
    serialized_form_set = serialize(form_set_with_errors, generated_schema)
    assert "name" in serialized_form_set.forms[0].errors
