from typing import Any, Dict, List, NamedTuple, Tuple

from django.db import models as django_models

from reactivated import create_schema
from reactivated.pick import build_nested_schema, get_field_descriptor
from sample.server.apps.samples import models


class NamedTupleType(NamedTuple):
    first: str
    second: bool
    third: int


def test_named_tuple():
    definitions = {}
    assert create_schema(NamedTupleType, definitions) == {
        "$ref": "#/definitions/tests.types.NamedTupleType"
    }
    assert definitions == {
        "tests.types.NamedTupleType": {
            "additionalProperties": False,
            "properties": {
                "first": {"type": "string"},
                "second": {"type": "boolean"},
                "third": {"type": "number"},
            },
            "required": ["first", "second", "third"],
            "type": "object",
        }
    }


def test_tuple():
    assert create_schema(Tuple[str, str], {}) == {
        "items": [{"type": "string"}, {"type": "string"}],
        "type": "array",
    }

    assert create_schema(Tuple[str, ...], {}) == {
        "items": {"type": "string"},
        "type": "array",
    }


def test_list():
    assert create_schema(List[str], {}) == {
        "type": "array",
        "items": {"type": "string"},
    }


def test_dict():
    assert create_schema(Dict[str, Any], {}) == {
        "type": "object",
        "additionalProperties": {},
    }

    assert create_schema(Dict[str, str], {}) == {
        "type": "object",
        "additionalProperties": {"type": "string"},
    }


def test_get_field_descriptor():
    descriptor, path = get_field_descriptor(models.Opera, ["has_piano_transcription"])
    assert isinstance(descriptor, django_models.BooleanField)
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ["composer"])
    assert isinstance(descriptor, django_models.ForeignKey)
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ["composer", "name"])
    assert isinstance(descriptor, django_models.CharField)
    assert path == (("composer", False),)

    descriptor, path = get_field_descriptor(
        models.Opera, ["composer", "countries", "name"]
    )
    assert isinstance(descriptor, django_models.CharField)
    assert path == (("composer", False), ("countries", True))

    descriptor, path = get_field_descriptor(
        models.Opera, ["composer", "composer_countries", "was_born"]
    )
    assert isinstance(descriptor, django_models.BooleanField)
    assert path == (("composer", False), ("composer_countries", True))

    descriptor, path = get_field_descriptor(models.Composer, ["countries"])
    assert isinstance(descriptor, django_models.ManyToManyField)
    assert path == ()


def test_build_nested_schema():
    """ This function mutates, so we test building multiple paths that are nested
    under the same object. """

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
        "required": [],
    }

    build_nested_schema(schema, (("a", False), ("b", False)))
    assert schema["properties"]["a"]["properties"]["b"]["type"] == "object"

    build_nested_schema(schema, (("a", False), ("c", False)))
    assert schema["properties"]["a"]["properties"]["b"]["type"] == "object"
    assert schema["properties"]["a"]["properties"]["c"]["type"] == "object"

    build_nested_schema(schema, (("a", False), ("multiple", True), ("single", False)))
    assert schema["properties"]["a"]["properties"]["multiple"]["type"] == "array"
    assert (
        schema["properties"]["a"]["properties"]["multiple"]["items"]["properties"][
            "single"
        ]["type"]
        == "object"
    )

    build_nested_schema(
        schema, (("a", False), ("multiple", True), ("second_single", False))
    )
    assert schema["properties"]["a"]["properties"]["multiple"]["type"] == "array"
    assert (
        schema["properties"]["a"]["properties"]["multiple"]["items"]["properties"][
            "single"
        ]["type"]
        == "object"
    )
    assert (
        schema["properties"]["a"]["properties"]["multiple"]["items"]["properties"][
            "second_single"
        ]["type"]
        == "object"
    )
