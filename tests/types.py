import enum
from io import StringIO
from typing import (
    Any,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypedDict,
    Union,
)

import pytest
import simplejson
from django import forms as django_forms
from django.core.exceptions import FieldDoesNotExist
from django.core.management import call_command
from django.db import models as django_models

from reactivated.fields import EnumField
from reactivated.models import ComputedRelation
from reactivated.pick import build_nested_schema, get_field_descriptor
from reactivated.serialization import ComputedField, create_schema
from reactivated.serialization.context_processors import create_context_processor_type
from sample.server.apps.samples import forms, models

from .serialization import convert_to_json_and_validate


class NamedTupleType(NamedTuple):
    first: str
    second: bool
    third: int

    @property
    def fourth_as_property(self) -> int:
        return 5


class TypedDictType(TypedDict):
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
                    "fourth_as_property": {"type": "number"},
                },
                "required": ["first", "second", "third", "fourth_as_property"],
                "serializer": None,
                "type": "object",
            }
        },
    )


class EnumType(enum.Enum):
    ONE = "One"
    TWO = "Two"
    CHUNK = NamedTupleType(first="a", second=True, third=4)


def test_enum():
    assert create_schema(EnumType, {}) == (
        {"$ref": "#/definitions/tests.types.EnumType"},
        {
            "tests.types.EnumType": {
                "type": "string",
                "enum": ["ONE", "TWO", "CHUNK"],
                "serializer": "reactivated.serialization.EnumMemberType",
            }
        },
    )


def test_enum_type():
    assert create_schema(Type[EnumType], {}) == (
        {"$ref": "#/definitions/tests.types.EnumTypeEnumType"},
        {
            "tests.types.EnumTypeEnumType": {
                "additionalProperties": False,
                "properties": {
                    "CHUNK": {
                        "$ref": "#/definitions/tests.types.NamedTupleType",
                        "serializer": "reactivated.serialization.EnumValueType",
                    },
                    "ONE": {
                        "serializer": "reactivated.serialization.EnumValueType",
                        "type": "string",
                    },
                    "TWO": {
                        "serializer": "reactivated.serialization.EnumValueType",
                        "type": "string",
                    },
                },
                "required": ["ONE", "TWO", "CHUNK"],
                "type": "object",
            },
            "tests.types.NamedTupleType": {
                "additionalProperties": False,
                "properties": {
                    "first": {"type": "string"},
                    "fourth_as_property": {"type": "number"},
                    "second": {"type": "boolean"},
                    "third": {"type": "number"},
                },
                "required": ["first", "second", "third", "fourth_as_property"],
                "serializer": None,
                "type": "object",
            },
        },
    )


def test_enum_does_not_clobber_enum_type():
    schema = create_schema(EnumType, {})
    schema = create_schema(Type[EnumType], schema.definitions)
    assert "tests.types.EnumType" in schema.definitions
    assert "tests.types.EnumTypeEnumType" in schema.definitions


def test_literal():
    schema = create_schema(Literal["hello"], {})
    assert schema == (
        {
            "type": "string",
            "enum": [
                "hello",
            ],
        },
        {},
    )
    convert_to_json_and_validate("hello", schema)


def test_typed_dict():
    assert create_schema(TypedDictType, {}) == (
        {"$ref": "#/definitions/tests.types.TypedDictType"},
        {
            "tests.types.TypedDictType": {
                "additionalProperties": False,
                "properties": {
                    "first": {"type": "string"},
                    "second": {"type": "boolean"},
                    "third": {"type": "number"},
                },
                "required": ["first", "second", "third"],
                "serializer": None,
                "type": "object",
            }
        },
    )


def test_fixed_tuple():
    assert create_schema(Tuple[str, str], {}) == (
        {
            "items": [{"type": "string"}, {"type": "string"}],
            "minItems": 2,
            "maxItems": 2,
            "type": "array",
        },
        {},
    )


def test_open_tuple():
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


def test_float():
    assert create_schema(float, {}) == ({"type": "number"}, {})


def test_int():
    assert create_schema(int, {}) == ({"type": "number"}, {})


@pytest.mark.skip
def test_form():
    schema = create_schema(forms.OperaForm, {})

    assert schema.schema == {
        "$ref": "#/definitions/sample.server.apps.samples.forms.OperaForm"
    }

    assert schema.definitions["sample.server.apps.samples.forms.OperaForm"] == {
        "additionalProperties": False,
        "properties": {
            "name": {
                "enum": ["sample.server.apps.samples.forms.OperaForm"],
                "type": "string",
            },
            "errors": {
                "anyOf": [
                    {
                        "additionalProperties": False,
                        "properties": {
                            "composer": {"items": {"type": "string"}, "type": "array"},
                            "has_piano_transcription": {
                                "items": {"type": "string"},
                                "type": "array",
                            },
                            "name": {"items": {"type": "string"}, "type": "array"},
                            "style": {"items": {"type": "string"}, "type": "array"},
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
                            "widget": {"tsType": "widgets.Select"},
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
                            "widget": {"tsType": "widgets.CheckboxInput"},
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
                            "widget": {"tsType": "widgets.TextInput"},
                        },
                        "required": ["name", "label", "help_text", "widget"],
                        "serializer": "field_serializer",
                        "type": "object",
                    },
                    "style": {
                        "additionalProperties": False,
                        "properties": {
                            "help_text": {"type": "string"},
                            "label": {"type": "string"},
                            "name": {"type": "string"},
                            "widget": {
                                "tsType": 'widgets.Select<Types["globals"]["SampleServerAppsSamplesModelsOperaStyle"]>'
                            },
                        },
                        "required": ["name", "label", "help_text", "widget"],
                        "serializer": "field_serializer",
                        "type": "object",
                    },
                },
                "required": ["name", "composer", "style", "has_piano_transcription"],
                "type": "object",
            },
            "iterator": {
                "items": {
                    "enum": ["name", "composer", "style", "has_piano_transcription"],
                    "type": "string",
                },
                "type": "array",
            },
            "prefix": {"type": "string"},
        },
        "required": ["name", "prefix", "fields", "iterator", "errors"],
        "serializer": "reactivated.serialization.FormType",
        "type": "object",
    }


def test_form_set():
    schema = create_schema(forms.OperaFormSet, {})

    assert schema.schema == {
        "$ref": "#/definitions/django.forms.formsets.OperaFormFormSet"
    }
    # Ensure the children of the child form are serialized by passing
    # definitions around without mutating.
    assert "sample.server.apps.samples.models.Opera.Style" in schema.definitions


def test_empty_form():
    class EmptyForm(django_forms.Form):
        pass

    assert create_schema(EmptyForm, {}).definitions[
        "tests.types.test_empty_form.<locals>.EmptyForm"
    ]["properties"]["iterator"] == {"items": [], "type": "array"}


class CustomField:
    pass


def custom_schema(Type, definitions):
    if issubclass(Type, CustomField):
        return create_schema(str, definitions)

    return None


def test_custom_schema(settings):
    with pytest.raises(AssertionError, match="Unsupported"):
        create_schema(CustomField, {})

    settings.REACTIVATED_SERIALIZATION = "tests.types.custom_schema"

    create_schema(CustomField, {}) == ({"type": "string"}, {})


def test_enum_field_descriptor():
    descriptor = EnumField(enum=EnumType)
    assert create_schema(descriptor, {}) == (
        {"$ref": "#/definitions/tests.types.EnumType"},
        {
            "tests.types.EnumType": {
                "type": "string",
                "enum": ["ONE", "TWO", "CHUNK"],
                "serializer": "reactivated.serialization.EnumMemberType",
            }
        },
    )


def test_get_field_descriptor():
    descriptor, path = get_field_descriptor(models.Opera, ["pk"])
    assert isinstance(descriptor.descriptor, django_models.AutoField)
    assert descriptor.descriptor.name == "id"
    assert descriptor.target_name == "pk"
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ["has_piano_transcription"])
    assert isinstance(descriptor.descriptor, django_models.BooleanField)
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ["composer"])
    assert isinstance(descriptor.descriptor, django_models.ForeignKey)
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ["composer", "name"])
    assert isinstance(descriptor.descriptor, django_models.CharField)
    assert path == (("composer", False, False),)

    descriptor, path = get_field_descriptor(
        models.Opera, ["composer", "countries", "name"]
    )
    assert isinstance(descriptor.descriptor, django_models.CharField)
    assert path == (("composer", False, False), ("countries", True, False))

    descriptor, path = get_field_descriptor(
        models.Opera, ["composer", "composer_countries", "was_born"]
    )
    assert isinstance(descriptor.descriptor, django_models.BooleanField)
    assert path == (("composer", False, False), ("composer_countries", True, False))

    descriptor, path = get_field_descriptor(models.Composer, ["countries"])
    assert isinstance(descriptor.descriptor, django_models.ManyToManyField)
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ["has_piano_transcription"])
    assert isinstance(descriptor.descriptor, django_models.BooleanField)
    assert path == ()

    with pytest.raises(FieldDoesNotExist):
        get_field_descriptor(models.Opera, ["does_not_exist"])

    descriptor, path = get_field_descriptor(
        models.Opera, ["get_birthplace_of_composer"]
    )
    assert isinstance(descriptor.descriptor, ComputedField)
    assert descriptor.descriptor.name == "get_birthplace_of_composer"
    assert descriptor.descriptor.annotation == Union[str, None]

    descriptor, path = get_field_descriptor(
        models.Opera, ["composer", "favorite_opera"]
    )
    assert isinstance(descriptor.descriptor, ComputedRelation)

    descriptor, path = get_field_descriptor(
        models.Opera, ["composer", "favorite_opera", "composer"]
    )
    assert isinstance(descriptor.descriptor, django_models.ForeignKey)
    assert path == (("composer", False, False), ("favorite_opera", False, True))


def test_build_nested_schema():
    """This function mutates, so we test building multiple paths that are nested
    under the same object."""

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
        "required": [],
    }

    build_nested_schema(schema, (("a", False, False), ("b", False, False)))
    assert schema["properties"]["a"]["properties"]["b"]["type"] == "object"

    build_nested_schema(schema, (("a", False, False), ("c", False, False)))
    assert schema["properties"]["a"]["properties"]["b"]["type"] == "object"
    assert schema["properties"]["a"]["properties"]["c"]["type"] == "object"

    build_nested_schema(
        schema,
        (("a", False, False), ("multiple", True, False), ("single", False, False)),
    )
    assert schema["properties"]["a"]["properties"]["multiple"]["type"] == "array"
    assert (
        schema["properties"]["a"]["properties"]["multiple"]["items"]["properties"][
            "single"
        ]["type"]
        == "object"
    )

    build_nested_schema(
        schema,
        (
            ("a", False, False),
            ("multiple", True, False),
            ("second_single", False, False),
        ),
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


@pytest.mark.skip(reason="needs to be an e2e test with node")
def test_generate_client_assets(settings):
    # This technically loads the full sample site, which expects to be run
    # from the sample subdirectory.
    settings.ROOT_URLCONF = "sample.server.urls"
    output = StringIO()
    call_command("generate_client_assets", stdout=output)
    schema = simplejson.loads(output.getvalue())
    assert "types" in schema
    assert "urls" in schema
    assert "templates" in schema


class ComplexType(TypedDict):
    required: int
    optional: Optional[bool]


class SampleContextOne(TypedDict):
    complex: ComplexType
    boolean: bool


class SampleContextTwo(TypedDict):
    number: int


def sample_context_processor_one() -> SampleContextOne:
    return {
        "complex": {
            "required": 5,
            "optional": True,
        },
        "boolean": True,
    }


def sample_context_processor_two() -> SampleContextTwo:
    return {
        "number": 5,
    }


def sample_unannotated_context_processor():
    pass


def test_context_processor_type():
    with pytest.raises(AssertionError, match="No annotations found"):
        ContextProcessorType = create_context_processor_type(
            ["tests.types.sample_unannotated_context_processor"]
        )

    context_processors = [
        "django.template.context_processors.request",
        "tests.types.sample_context_processor_one",
        "tests.types.sample_context_processor_two",
    ]

    ContextProcessorType = create_context_processor_type(context_processors)
    schema, definitions = create_schema(ContextProcessorType, {})

    assert schema == {
        "allOf": [
            {
                "$ref": "#/definitions/reactivated.serialization.context_processors.BaseContext"
            },
            {
                "$ref": "#/definitions/reactivated.serialization.context_processors.RequestProcessor"
            },
            {"$ref": "#/definitions/tests.types.SampleContextOne"},
            {"$ref": "#/definitions/tests.types.SampleContextTwo"},
        ]
    }
    assert definitions == {
        "reactivated.serialization.context_processors.BaseContext": {
            "serializer": None,
            "type": "object",
            "additionalProperties": False,
            "properties": {"template_name": {"type": "string"}},
            "required": ["template_name"],
        },
        "reactivated.serialization.context_processors.Request": {
            "serializer": "reactivated.serialization.context_processors.Request",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {"type": "string"},
                "url": {"type": "string"},
                "csp_nonce": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            },
            "required": ["path", "url", "csp_nonce"],
        },
        "reactivated.serialization.context_processors.RequestProcessor": {
            "serializer": None,
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "request": {
                    "$ref": "#/definitions/reactivated.serialization.context_processors.Request"
                }
            },
            "required": ["request"],
        },
        "tests.types.ComplexType": {
            "serializer": None,
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "required": {"type": "number"},
                "optional": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
            },
            "required": ["required", "optional"],
        },
        "tests.types.SampleContextOne": {
            "serializer": None,
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "complex": {"$ref": "#/definitions/tests.types.ComplexType"},
                "boolean": {"type": "boolean"},
            },
            "required": ["complex", "boolean"],
        },
        "tests.types.SampleContextTwo": {
            "serializer": None,
            "type": "object",
            "additionalProperties": False,
            "properties": {"number": {"type": "number"}},
            "required": ["number"],
        },
    }
