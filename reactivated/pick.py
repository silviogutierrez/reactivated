from __future__ import annotations

from typing import Any, List, Literal, Sequence, Tuple, Type, get_type_hints

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from .models import ComputedRelation
from .serialization import (
    ComputedField,
    Definitions,
    FieldDescriptor,
    Thing,
    create_schema,
)

FieldSegment = Tuple[str, bool]

JSONSchema = Any


def get_field_descriptor(
    model_class: Type[models.Model], field_chain: List[str]
) -> Tuple[FieldDescriptor, Sequence[FieldSegment]]:
    field_name, *remaining = field_chain

    try:
        field_descriptor: FieldDescriptor = model_class._meta.get_field(field_name)
    except FieldDoesNotExist as e:
        possible_method_or_property = getattr(model_class, field_name, None)

        if isinstance(possible_method_or_property, ComputedRelation):
            field_descriptor = possible_method_or_property
        elif possible_method_or_property is not None:
            # TODO: stronger checks here. This could just be a random method with
            # more than the `self` argument. Which would fail at runtime.
            possible_method, is_callable = (
                (possible_method_or_property.fget, False)
                if isinstance(possible_method_or_property, property)
                else (possible_method_or_property, True)
            )
            annotations = get_type_hints(possible_method)

            field_descriptor = ComputedField(
                name=field_name,
                annotation=annotations["return"],
                is_callable=is_callable,
            )
        else:
            raise e

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
            ComputedRelation,
            # TODO: Maybe RelatedField replaces all of the above?
            models.fields.related.RelatedField,
        ),
    ):
        nested_descriptor, nested_field_names = get_field_descriptor(
            field_descriptor.related_model, remaining
        )

        # TODO: Maybe RelatedField replaces all of the above?
        # Consolidate around many_* properties
        # OneToOneRel is a subclass of ManyToOneRel so we need to short circuit.
        is_multiple = (
            not isinstance(field_descriptor, models.OneToOneRel)
            and isinstance(
                field_descriptor, (models.ManyToManyField, models.ManyToOneRel)
            )
        ) or field_descriptor.many_to_many is True

        return nested_descriptor, ((field_name, is_multiple), *nested_field_names)

    assert False, "Unknown descriptor"


def serialize(instance: models.Model, schema: JSONSchema) -> Any:
    serialized = {}

    for field_name, field in schema["properties"].items():
        if field["type"] == "array":
            related_manager = getattr(instance, field_name)
            serialized[field_name] = [
                serialize(nested_instance, field["items"])
                for nested_instance in related_manager.all()
            ]
        elif field["type"] == "object":
            nested_instance = getattr(instance, field_name)
            serialized[field_name] = serialize(nested_instance, field)
        else:
            serialized[field_name] = getattr(instance, field_name)

    return serialized


def build_nested_schema(schema: JSONSchema, path: Sequence[FieldSegment]) -> JSONSchema:
    for item, is_multiple in path:
        existing_subschema = schema["properties"].get(item)

        if is_multiple:
            if existing_subschema is None:
                schema["properties"][item] = {
                    "type": "array",
                    "serializer": "reactivated.serialization.QuerySetType",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {},
                        "required": [],
                    },
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


class BasePickHolder:
    model_class: Type[models.Model]
    fields: List[str] = []

    @classmethod
    def get_json_schema(cls: Type[BasePickHolder], definitions: Definitions) -> Thing:
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
            reference = build_nested_schema(schema, path)

            field_schema = create_schema(field_descriptor, definitions)
            definitions = {**definitions, **field_schema.definitions}

            reference["properties"][field_descriptor.name] = field_schema.schema
            reference["required"].append(field_descriptor.name)

        return Thing(schema=schema, definitions=definitions)


class Pick:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        meta_model, *meta_fields = item

        if isinstance(meta_model, str):
            nested_fields = []

            for nested_field in meta_fields[0].fields:
                nested_fields.append(f"{meta_model}.{nested_field}")
            return nested_fields

        flattened_fields: List[str] = []

        for field_or_literal in meta_fields:
            if isinstance(field_or_literal, str):
                flattened_fields.append(field_or_literal)
            elif isinstance(field_or_literal, list):
                flattened_fields.extend(field_or_literal)
            elif field_or_literal.__origin__ == Literal:
                flattened_fields.extend(field_or_literal.__args__)
            else:
                assert False, f"Unsupported pick property {field_or_literal}"

        class PickHolder(BasePickHolder):
            model_class = meta_model
            fields = flattened_fields

        return PickHolder
