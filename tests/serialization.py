import pytest

from typing import List, NamedTuple

from reactivated import Pick, create_schema
from sample.server.apps.samples import models

schema = {
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
}


def object_serializer(value, schema):
    representation = {}

    for field_name, field_schema in schema["properties"].items():
        attribute = getattr(value, field_name)

        representation[field_name] = serialize(attribute, field_schema)

    return representation


def array_serializer(value, schema):
    # TODO: this could be the tuple type.
    item_schema = schema["items"]

    return [serialize(item, item_schema) for item in value]


def queryset_serializer(value, schema):
    return [serialize(item, schema["items"]) for item in value.all()]


SERIALIZERS = {
    "object": object_serializer,
    "string": lambda value, schema: str(value),
    "boolean": lambda value, schema: bool(value),
    "array": array_serializer,
    "queryset": queryset_serializer,
}


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


def serialize(value, schema):
    serializer = SERIALIZERS.get(schema.get("serializer", schema["type"]), None)
    assert serializer is not None

    return serializer(value, schema)


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
    generated_schema = create_schema(Foo, definitions, ref=False)

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


def test_create_schema():
    from reactivated.serialization import create_schema
    from typing import Union
    schema = create_schema(Union[str, bool], {})
    foo = create_schema(Foo, {})
    import pprint
    pprint.pprint(foo.schema)
    pprint.pprint(foo.definitions)
    assert False
