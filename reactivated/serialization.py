from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Type, Union

import simplejson
from django import forms as django_forms
from django.db.models import QuerySet

from . import stubs

Schema = Mapping[Any, Any]

Definitions = Mapping[str, Schema]

JSON = Any


FormError = Optional[List[str]]

FormErrors = Dict[str, FormError]


class WidgetType(NamedTuple):
    @classmethod
    def get_json_schema(Type: Type["WidgetType"], definitions: Definitions) -> "Thing":
        return Thing(schema={"tsType": str(Type.__name__)}, definitions=definitions)


class FieldType(NamedTuple):
    name: str
    label: str
    help_text: str
    widget: WidgetType

    @classmethod
    def get_json_schema(Type: Type["FieldType"], definitions: Definitions) -> "Thing":
        definition_name = f"{Type.__module__}.{Type.__qualname__}"

        if definition_name in definitions:
            return Thing(
                schema={"$ref": f"#/definitions/{definition_name}"},
                definitions=definitions,
            )

        schema = named_tuple_schema(Type, definitions)

        definitions = {
            **definitions,
            definition_name: {
                **schema.definitions[definition_name],
                "serializer": "field_serializer",
            },
        }

        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )


class FormType(NamedTuple):
    errors: Optional[FormErrors]
    fields: Dict[str, FieldType]
    iterator: List[str]
    prefix: str


class FormSetType(NamedTuple):
    initial: int
    total: int
    max_num: int
    min_num: int
    can_delete: bool
    can_order: bool
    non_form_errors: List[str]

    forms: List[FormType]
    empty_form: FormType
    management_form: FormType
    prefix: str


class Thing(NamedTuple):
    schema: Schema
    definitions: Definitions


def generic_alias_schema(Type: stubs._GenericAlias, definitions: Definitions) -> Thing:
    subschemas: Sequence[Schema]

    if Type.__origin__ == tuple:
        *tuple_args, last_arg = Type.__args__

        if last_arg is Ellipsis:
            items_schema = create_schema(tuple_args[0], definitions)

            return Thing(
                schema={"type": "array", "items": items_schema.schema},
                definitions=items_schema.definitions,
            )

        subschemas = []

        for subtype in Type.__args__:
            subschema = create_schema(subtype, definitions=definitions)
            subschemas = [*subschemas, subschema.schema]
            definitions = {**definitions, **subschema.definitions}

        return Thing(
            schema={"type": "array", "items": subschemas}, definitions=definitions
        )
    elif Type.__origin__ == Union:
        subschemas = ()

        for subtype in Type.__args__:
            subschema = create_schema(subtype, definitions=definitions)
            subschemas = [*subschemas, subschema.schema]
            definitions = {**definitions, **subschema.definitions}

        return Thing(schema={"anyOf": subschemas}, definitions=definitions)
    elif Type.__origin__ == list:
        subschema = create_schema(Type.__args__[0], definitions=definitions)
        return Thing(
            schema={"type": "array", "items": subschema.schema},
            definitions=subschema.definitions,
        )
    elif Type.__origin__ == dict:
        subschema = create_schema(Type.__args__[1], definitions=definitions)

        return Thing(
            schema={
                "type": "object",
                "properties": {},
                "additionalProperties": subschema.schema,
            },
            definitions=subschema.definitions,
        )
    assert False, f"Unsupported _GenericAlias {Type}"


def named_tuple_schema(Type: Any, definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    required = []
    properties = {}
    definitions = {**definitions}

    for field_name, Subtype in Type.__annotations__.items():
        field_schema = create_schema(Subtype, definitions)
        definitions = {**definitions, **field_schema.definitions}

        required.append(field_name)
        properties[field_name] = field_schema.schema

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"},
        definitions={
            **definitions,
            definition_name: {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required,
            },
        },
    )


def form_schema(Type: Type[django_forms.BaseForm], definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    schema = named_tuple_schema(FormType, definitions)
    """
    form_type_definition = schema.definitions[
        f"{FormType.__module__}.{FormType.__qualname__}"
    ]
    """
    field_type_definition = schema.definitions[
        f"{FieldType.__module__}.{FieldType.__qualname__}"
    ]

    error_definition = create_schema(
        FormError, definitions  # type: ignore[misc]
    ).schema

    required = []
    properties = {}
    error_properties = {}

    for field_name, SubType in Type.base_fields.items():  # type: ignore[attr-defined]
        required.append(field_name)
        properties[field_name] = field_type_definition
        error_properties[field_name] = error_definition

    definitions = {
        **definitions,
        definition_name: {
            "type": "object",
            "properties": {
                "errors": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": error_properties,
                            "additionalProperties": False,
                        },
                        {"type": "null"},
                    ]
                },
                "fields": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                "prefix": {"type": "string"},
                "iterator": {
                    "type": "array",
                    "items": {"enum": required, "type": "string"},
                },
            },
            "serializer": "form_serializer",
            "additionalProperties": False,
            "required": ["prefix", "fields", "iterator", "errors"],
        },
    }

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
    )


def form_set_schema(Type: Type[stubs.BaseFormSet], definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    form_set_type_schema = create_schema(FormSetType, definitions)

    if issubclass(Type, django_forms.BaseModelFormSet):
        pk_field_name = Type.model._meta.pk.name
        FormSetForm = type(
            "FormSetForm", (Type.form,), {pk_field_name: django_forms.Field()}
        )
    else:
        FormSetForm = Type.form

    form_type_schema = create_schema(FormSetForm, form_set_type_schema.definitions)

    # We use our own management form because base_fields is set dynamically
    # by Django in django.forms.formsets.
    class ManagementForm(django_forms.formsets.ManagementForm):
        base_fields: Any

    ManagementForm.base_fields = ManagementForm().base_fields

    management_form_schema = create_schema(ManagementForm, form_type_schema.definitions)

    form_set_type_definition = form_set_type_schema.definitions[
        f"{FormSetType.__module__}.{FormSetType.__qualname__}"
    ]

    form_type_definition = form_type_schema.definitions[
        f"{FormSetForm.__module__}.{FormSetForm.__qualname__}"  # type: ignore[attr-defined]
    ]

    management_form_definition = management_form_schema.definitions[
        f"{ManagementForm.__module__}.{ManagementForm.__qualname__}"
    ]

    definitions = {
        **definitions,
        definition_name: {
            **form_set_type_definition,
            "serializer": "form_set_serializer",
            "properties": {
                **form_set_type_definition["properties"],
                "empty_form": form_type_definition,
                "forms": {"type": "array", "items": form_type_definition},
                "management_form": management_form_definition,
            },
        },
    }

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
    )


def create_schema(Type: Any, definitions: Definitions) -> Thing:
    if isinstance(Type, stubs._GenericAlias):
        return generic_alias_schema(Type, definitions)
    elif Type == Any:
        return Thing(schema={}, definitions=definitions)
    elif callable(getattr(Type, "get_json_schema", None)):
        return Type.get_json_schema(definitions)  # type: ignore[no-any-return]
    elif issubclass(Type, tuple) and callable(getattr(Type, "_asdict", None)):
        return named_tuple_schema(Type, definitions)
    elif issubclass(Type, bool):
        return Thing(schema={"type": "boolean"}, definitions={})
    elif issubclass(Type, int):
        return Thing(schema={"type": "number"}, definitions={})
    elif issubclass(Type, str):
        return Thing(schema={"type": "string"}, definitions={})
    elif Type is type(None):  # noqa: E721
        return Thing(schema={"type": "null"}, definitions={})
    elif issubclass(Type, django_forms.BaseForm):
        return form_schema(Type, definitions)
    elif issubclass(Type, stubs.BaseFormSet):
        return form_set_schema(Type, definitions)
    assert False, f"Unsupported type {Type}"


def object_serializer(value: object, schema: Thing) -> JSON:
    representation = {}

    for field_name, field_schema in schema.schema["properties"].items():
        attribute = (
            value.get(field_name, None)
            if isinstance(value, Mapping)
            else getattr(value, field_name, None)
        )

        representation[field_name] = serialize(
            attribute, Thing(schema=field_schema, definitions=schema.definitions)
        )

    additional_properties_schema = schema.schema["additionalProperties"]

    if additional_properties_schema and isinstance(value, Mapping):
        return {
            **representation,
            **{
                field_name: serialize(
                    field_value,
                    Thing(
                        schema=additional_properties_schema,
                        definitions=schema.definitions,
                    ),
                )
                for field_name, field_value in value.items()
                if field_name not in schema.schema["properties"]
            },
        }

    return representation


def array_serializer(value: Sequence[Any], schema: Thing) -> JSON:
    item_schema = schema.schema["items"]

    # For fixed tuples, though the JSON schema will actually be a list as JSON
    # has no concept of tuples.
    if isinstance(item_schema, list):
        return [
            serialize(
                item, Thing(schema=item_schema_member, definitions=schema.definitions)
            )
            for item, item_schema_member in zip(value, item_schema)
        ]

    return [
        serialize(item, Thing(schema=item_schema, definitions=schema.definitions))
        for item in value
    ]


def queryset_serializer(value: "QuerySet[Any]", schema: Thing) -> JSON:
    return [
        serialize(
            item, Thing(schema=schema.schema["items"], definitions=schema.definitions)
        )
        for item in value.all()
    ]


def form_serializer(value: django_forms.BaseForm, schema: Thing) -> JSON:
    from . import SSRFormRenderer

    form = value

    form.renderer = SSRFormRenderer()
    fields = {
        field.name: FieldType(
            widget=simplejson.loads(str(field))["widget"],
            name=field.name,
            label=str(
                field.label
            ),  # This can be a lazy proxy, so we must call str on it.
            help_text=str(
                field.help_text
            ),  # This can be a lazy proxy, so we must call str on it.
        )
        for field in form
    }

    return FormType(
        errors=form.errors or None,
        fields=fields,
        iterator=list(fields.keys()),
        prefix=form.prefix or "",
    )


def form_set_serializer(value: stubs.BaseFormSet, schema: Thing) -> JSON:
    form_set = value
    form_schema = create_schema(form_set.form, schema.definitions)

    return FormSetType(
        initial=form_set.initial_form_count(),
        total=form_set.total_form_count(),
        max_num=form_set.max_num,
        min_num=form_set.min_num,
        can_delete=form_set.can_delete,
        can_order=form_set.can_order,
        non_form_errors=form_set.non_form_errors(),
        forms=[serialize(form, form_schema) for form in form_set],
        empty_form=serialize(form_set.empty_form, form_schema),
        management_form=serialize(form_set.management_form, form_schema),
        prefix=form_set.prefix,
    )


SERIALIZERS = {
    "any": lambda value, schema: value,
    "object": object_serializer,
    "string": lambda value, schema: str(value),
    "boolean": lambda value, schema: bool(value),
    "number": lambda value, schema: int(value),
    "array": array_serializer,
    "queryset": queryset_serializer,
    "form_serializer": form_serializer,
    "form_set_serializer": form_set_serializer,
}


def serialize(value: Any, schema: Thing) -> JSON:
    if value is None:
        return None

    dereferenced_schema = (
        schema.definitions[schema.schema["$ref"].replace("#/definitions/", "")]
        if "$ref" in schema.schema
        else schema.schema
    )

    if "anyOf" in dereferenced_schema:
        for any_of_schema in dereferenced_schema["anyOf"]:
            return serialize(
                value, Thing(schema=any_of_schema, definitions=schema.definitions)
            )

    serializer = SERIALIZERS.get(
        dereferenced_schema.get("serializer", dereferenced_schema.get("type", "any")),
        None,
    )
    assert serializer is not None

    return serializer(
        value, Thing(schema=dereferenced_schema, definitions=schema.definitions)
    )
