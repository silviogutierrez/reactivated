from __future__ import annotations

from django.db import models

from typing import Any, List, Type

FieldDescriptor = Any


def get_field_descriptor(model_class: Type[models.Model], field_chain: List[str]) -> models.Field[Any, Any]:
    field_name, *remaining = field_chain

    field_descriptor = model_class._meta.get_field(field_name)

    if isinstance(field_descriptor, (models.ForeignKey, models.OneToOneField, models.ManyToOneRel)):
        nested_descriptor, nested_field_names = get_field_descriptor(field_descriptor.related_model, remaining)
        return nested_descriptor, ((field_name, True), *nested_field_names)

    return field_descriptor, ((field_name, False),)


MAPPING = {
    models.CharField: "string",
    models.BooleanField: "boolean",
}


class BasePickHolder:
    model: Type[models.Model]
    fields: List[str] = []

    @classmethod
    def get_json_schema(cls) -> Any:
        properties = {}
        required = []

        for field_name in cls.fields:
            field_descriptor = cls.model._meta.get_field(field_name)
            json_schema_type = MAPPING.get(field_descriptor.__class__)

            if json_schema_type:
                properties[field_name] = {"type": json_schema_type}
            else:
                properties[field_name] = {}

            required.append(field_name)

        definition = {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
        }

        return definition


class Pick:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        meta_model, *meta_fields = item

        class PickHolder(BasePickHolder):
            model = meta_model
            fields = meta_fields

        return PickHolder
