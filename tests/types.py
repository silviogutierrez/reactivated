from io import StringIO
from typing import Any, Dict, List, NamedTuple, Tuple

import simplejson
from django.core.management import call_command
from django.db import models as django_models

from reactivated.pick import build_nested_schema, get_field_descriptor
from reactivated.serialization import create_schema
from sample.server.apps.samples import forms, models


class NamedTupleType(NamedTuple):
    first: str
    second: bool
    third: int


def test_named_tuple():
    assert create_schema(NamedTupleType, {}) == (
        {"$ref": "#/definitions/tests.types.NamedTupleType"},
        {
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
        },
    )


def test_tuple():
    assert create_schema(Tuple[str, str], {}) == (
        {"items": [{"type": "string"}, {"type": "string"}], "type": "array"},
        {},
    )

    assert create_schema(Tuple[str, ...], {}) == (
        {"items": {"type": "string"}, "type": "array"},
        {},
    )


def test_list():
    assert create_schema(List[str], {}) == (
        {"type": "array", "items": {"type": "string"}},
        {},
    )


def test_dict():
    assert create_schema(Dict[str, Any], {}) == (
        {"type": "object", "properties": {}, "additionalProperties": {}},
        {},
    )

    assert create_schema(Dict[str, str], {}) == (
        {
            "type": "object",
            "properties": {},
            "additionalProperties": {"type": "string"},
        },
        {},
    )


def test_none():
    assert create_schema(type(None), {}) == ({"type": "null"}, {})


def test_form():
    schema = create_schema(forms.OperaForm, {})

    assert schema.schema == {
        "$ref": "#/definitions/sample.server.apps.samples.forms.OperaForm"
    }

    assert schema.definitions["sample.server.apps.samples.forms.OperaForm"] == {
        "additionalProperties": False,
        "properties": {
            "errors": {
                "anyOf": [
                    {
                        "additionalProperties": False,
                        "properties": {
                            "composer": {
                                "anyOf": [
                                    {"items": {"type": "string"}, "type": "array"},
                                    {"type": "null"},
                                ]
                            },
                            "has_piano_transcription": {
                                "anyOf": [
                                    {"items": {"type": "string"}, "type": "array"},
                                    {"type": "null"},
                                ]
                            },
                            "name": {
                                "anyOf": [
                                    {"items": {"type": "string"}, "type": "array"},
                                    {"type": "null"},
                                ]
                            },
                        },
                        "type": "object",
                    },
                    {"type": "null"},
                ]
            },
            "fields": {
                "additionalProperties": False,
                "properties": {
                    "composer": {
                        "additionalProperties": False,
                        "properties": {
                            "help_text": {"type": "string"},
                            "label": {"type": "string"},
                            "name": {"type": "string"},
                            "widget": {"tsType": "WidgetType"},
                        },
                        "required": ["name", "label", "help_text", "widget"],
                        "serializer": "field_serializer",
                        "type": "object",
                    },
                    "has_piano_transcription": {
                        "additionalProperties": False,
                        "properties": {
                            "help_text": {"type": "string"},
                            "label": {"type": "string"},
                            "name": {"type": "string"},
                            "widget": {"tsType": "WidgetType"},
                        },
                        "required": ["name", "label", "help_text", "widget"],
                        "serializer": "field_serializer",
                        "type": "object",
                    },
                    "name": {
                        "additionalProperties": False,
                        "properties": {
                            "help_text": {"type": "string"},
                            "label": {"type": "string"},
                            "name": {"type": "string"},
                            "widget": {"tsType": "WidgetType"},
                        },
                        "required": ["name", "label", "help_text", "widget"],
                        "serializer": "field_serializer",
                        "type": "object",
                    },
                },
                "required": ["name", "composer", "has_piano_transcription"],
                "type": "object",
            },
            "iterator": {
                "items": {
                    "enum": ["name", "composer", "has_piano_transcription"],
                    "type": "string",
                },
                "type": "array",
            },
            "prefix": {"type": "string"},
        },
        "required": ["prefix", "fields", "iterator", "errors"],
        "serializer": "form_serializer",
        "type": "object",
    }


def test_form_set():
    schema = create_schema(forms.OperaFormSet, {})

    assert schema.schema == {
        "$ref": "#/definitions/django.forms.formsets.OperaFormFormSet"
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


def test_generate_types_schema():
    output = StringIO()

    call_command("generate_types_schema", stdout=output)
    schema = simplejson.loads(output.getvalue())
    assert "types" in schema
    assert "urls" in schema
    assert "templates" in schema
