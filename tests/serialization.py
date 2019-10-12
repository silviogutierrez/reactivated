from typing import Iterable, NamedTuple

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


SERIALIZERS = {
    "object": object_serializer,
    "string": lambda value, schema: str(value),
    "boolean": lambda value, schema: bool(value),
    "array": array_serializer,
}


class Spam(NamedTuple):
    thing: Iterable[str]
    again: str


class Bar(NamedTuple):
    a: str
    b: bool


class Foo(NamedTuple):
    bar: Bar
    spam: Spam


def serialize(value, schema):
    serializer = SERIALIZERS.get(schema["type"], None)
    assert serializer is not None

    return serializer(value, schema)


def test_serialization():
    instance = Foo(
        bar=Bar(a="a", b=True),
        spam=Spam(thing=["one", "two", "three", "four"], again="ok"),
    )
    assert serialize(instance, schema) == {
        "bar": {"a": "a", "b": True},
        "spam": {"thing": ["one", "two", "three", "four"], "again": "ok"},
    }
