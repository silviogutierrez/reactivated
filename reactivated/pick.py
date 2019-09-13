from __future__ import annotations

from django.db import models

from typing import Any, List, Type, Sequence, Tuple, Dict

FieldDescriptor = Any

FieldSegment = Tuple[str, bool]

JSONSchema = Any


def get_field_descriptor(
    model_class: Type[models.Model], field_chain: List[str]
) -> Tuple[models.Field[Any, Any], Sequence[FieldSegment]]:
    field_name, *remaining = field_chain

    field_descriptor = model_class._meta.get_field(field_name)

    if len(remaining) == 0:
        return field_descriptor, ()
    elif isinstance(
        field_descriptor,
        (
            models.ForeignKey,
            models.OneToOneField,
            models.ManyToOneRel,
            models.ManyToManyField,
            models.ManyToOneRel,
        ),
    ):
        nested_descriptor, nested_field_names = get_field_descriptor(
            field_descriptor.related_model, remaining
        )

        is_multiple = isinstance(
            field_descriptor, (models.ManyToManyField, models.ManyToOneRel)
        )
        return nested_descriptor, ((field_name, is_multiple), *nested_field_names)

    assert False


def build_nested_schema(schema: JSONSchema, path: Sequence[FieldSegment]) -> JSONSchema:
    for item, is_multiple in path:
        existing_subschema = schema["properties"].get(item)

        if is_multiple:
            if existing_subschema is None:
                schema["properties"][item] = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {},
                        "required": [],
                    }
                }
                schema["required"].append(item)
            schema = schema["properties"][item]["items"]
        else:
            if existing_subschema is None:
                schema["properties"][item] = {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {},
                    "required": [],
                }
                schema["required"].append(item)
            schema = schema["properties"][item]
    return schema


MAPPING = {
    models.CharField: "string",
    models.BooleanField: "boolean",
    models.ForeignKey: "string",
}


class BasePickHolder:
    model_class: Type[models.Model]
    fields: List[str] = []

    @classmethod
    def get_json_schema(cls) -> Any:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
            "required": [],
        }

        for field_name in cls.fields:
            field_descriptor, path = get_field_descriptor(
                cls.model_class, field_name.split(".")
            )
            json_schema_type = MAPPING.get(field_descriptor.__class__)
            reference = build_nested_schema(schema, path)

            if json_schema_type:
                reference["properties"][field_descriptor.name] = {"type": json_schema_type}
            else:
                reference["properties"][field_descriptor.name] = {}
            reference["required"].append(field_descriptor.name)

        return schema


class Pick:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        meta_model, *meta_fields = item

        class PickHolder(BasePickHolder):
            model_class = meta_model
            fields = meta_fields

        return PickHolder
