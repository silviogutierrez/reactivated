from typing import List, NamedTuple

import pytest

from reactivated import Pick
from reactivated.serialization import Thing, create_schema, serialize
from sample.server.apps.samples import forms, models

schema = Thing(
    schema={
        "type": "object",
        "properties": {
            "bar": {
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "boolean"}},
            },
            "spam": {
                "type": "object",
                "properties": {
                    "thing": {"type": "array", "items": {"type": "string"}},
                    "again": {"type": "string"},
                },
            },
            "pick": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "operas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        },
                        "serializer": "queryset",
                    },
                },
            },
        },
    },
    definitions={},
)


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

    assert serialize(instance, schema) == {
        "bar": {"a": "a", "b": True},
        "spam": {"thing": ["one", "two", "three", "four"], "again": "ok"},
        "pick": {"name": composer.name, "operas": [{"name": opera.name}]},
    }

    assert serialize(instance, generated_schema) == {
        "bar": {"a": "a", "b": True},
        "spam": {"thing": ["one", "two", "three", "four"], "again": "ok"},
        "pick": {"name": composer.name, "operas": [{"name": opera.name}]},
    }


def test_form():
    generated_schema = create_schema(forms.OperaForm, {})
    form = forms.OperaForm()
    serialize(form, generated_schema)
