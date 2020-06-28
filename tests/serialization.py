from typing import Any, List, Literal, NamedTuple, Tuple

import pytest
import simplejson
from jsonschema import validate

from reactivated import Pick
from reactivated.serialization import create_schema, serialize
from sample.server.apps.samples import forms, models


class Spam(NamedTuple):
    thing: List[str]
    again: str


class Bar(NamedTuple):
    a: str
    b: bool


Opera = Pick[models.Opera, "name"]


class Foo(NamedTuple):
    bar: Bar
    spam: Spam
    pick: Pick[models.Composer, "name", "operas.name"]
    pick_many: List[Pick[models.Composer, "name", "operas.name"]]
    pick_method: Pick[models.Opera, "name", "get_birthplace_of_composer"]
    pick_property: Pick[models.Composer, "did_live_in_more_than_one_country"]
    pick_literal: Pick[models.Composer, Literal["name", "operas.name"]]
    pick_computed_queryset: Pick[
        models.Composer, "operas_with_piano_transcriptions.name"
    ]
    pick_nested: Pick[models.Composer, "name", Pick["operas", Opera]]
    fixed_tuple_different_types: Tuple[str, int]
    fixed_tuple_same_types: Tuple[str, str]
    complex_type_we_do_not_type: Any


def convert_to_json_and_validate(instance, schema):
    converted = simplejson.loads(simplejson.dumps(instance))
    validate(
        instance=converted, schema={"definitions": schema.definitions, **schema.schema}
    )


@pytest.mark.django_db
def test_serialization():
    continent = models.Continent.objects.create(name="Europe")
    birth_country = models.Country.objects.create(name="Germany", continent=continent)
    other = models.Country.objects.create(name="Switzerland", continent=continent)

    composer = models.Composer.objects.create(name="Wagner")
    models.ComposerCountry.objects.create(
        composer=composer, country=birth_country, was_born=True
    )
    models.ComposerCountry.objects.create(composer=composer, country=other)

    opera = models.Opera.objects.create(name="Götterdämmerung", composer=composer)

    instance = Foo(
        bar=Bar(a="a", b=True),
        spam=Spam(thing=["one", "two", "three", "four"], again="ok"),
        pick=composer,
        pick_many=list(models.Composer.objects.all()),
        pick_method=opera,
        pick_property=composer,
        pick_literal=composer,
        pick_computed_queryset=composer,
        pick_nested=composer,
        fixed_tuple_different_types=("ok", 5),
        fixed_tuple_same_types=("alright", "again"),
        complex_type_we_do_not_type={
            "I am": "very complex",
            "because": {"I am": "nested", "ok?": []},
        },
    )
    definitions = {}
    generated_schema = create_schema(Foo, definitions)

    serialized = serialize(instance, generated_schema)

    assert serialized == {
        "bar": {"a": "a", "b": True},
        "spam": {"thing": ["one", "two", "three", "four"], "again": "ok"},
        "pick": {"name": composer.name, "operas": [{"name": opera.name}]},
        "pick_many": [{"name": "Wagner", "operas": [{"name": "Götterdämmerung"}]}],
        "pick_method": {
            "name": "Götterdämmerung",
            "get_birthplace_of_composer": "Germany",
        },
        "pick_property": {"did_live_in_more_than_one_country": True,},
        "pick_literal": {"name": composer.name, "operas": [{"name": opera.name}]},
        "pick_computed_queryset": {
            "operas_with_piano_transcriptions": [{"name": "Götterdämmerung"}]
        },
        "pick_nested": {"name": composer.name, "operas": [{"name": opera.name}]},
        "fixed_tuple_different_types": ["ok", 5],
        "fixed_tuple_same_types": ["alright", "again"],
        "complex_type_we_do_not_type": {
            "I am": "very complex",
            "because": {"I am": "nested", "ok?": []},
        },
    }

    convert_to_json_and_validate(serialized, generated_schema)


def test_form():
    generated_schema = create_schema(forms.OperaForm, {})
    form = forms.OperaForm()
    serialized_form = serialize(form, generated_schema)
    convert_to_json_and_validate(serialized_form, generated_schema)

    form_with_errors = forms.OperaForm({})
    form_with_errors.is_valid()
    serialized_form = serialize(form_with_errors, generated_schema)
    assert "name" in serialized_form.errors
    convert_to_json_and_validate(serialized_form, generated_schema)


@pytest.mark.django_db
def test_form_set():
    generated_schema = create_schema(forms.OperaFormSet, {})
    form_set = forms.OperaFormSet()
    serialized_form_set = serialize(form_set, generated_schema)
    convert_to_json_and_validate(serialized_form_set, generated_schema)

    form_set_with_errors = forms.OperaFormSet(
        {"form-TOTAL_FORMS": 20, "form-INITIAL_FORMS": 0}
    )
    form_set_with_errors.is_valid()
    serialized_form_set = serialize(form_set_with_errors, generated_schema)
    assert "name" in serialized_form_set.forms[0].errors
    convert_to_json_and_validate(serialized_form_set, generated_schema)
