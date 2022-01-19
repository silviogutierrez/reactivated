from __future__ import annotations

from typing import (
    Any,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    get_type_hints,
)

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from .models import ComputedRelation
from .serialization import ComputedField, FieldDescriptor, create_schema
from .serialization.registry import Definitions, JSONSchema, Thing

FieldSegment = Tuple[str, bool, bool]


class FieldDescriptorWrapper(NamedTuple):
    descriptor: FieldDescriptor
    target_name: Optional[str] = None
    annotation: Optional[Any] = None


def get_field_descriptor(
    model_class: Type[models.Model], field_chain: List[str]
) -> Tuple[FieldDescriptorWrapper, Sequence[FieldSegment]]:
    field_name, *remaining = field_chain

    resolved_hints = (
        model_class.resolve_type_hints()  # type: ignore[attr-defined]
        if hasattr(model_class, "resolve_type_hints")
        else {}
    )

    try:
        overrides = get_type_hints(model_class, localns=resolved_hints)
        annotation = overrides.get(field_name, None)

        field_descriptor = (
            FieldDescriptorWrapper(descriptor=model_class._meta.pk, annotation=annotation, target_name="pk")  # type: ignore[arg-type]
            if field_name == "pk"
            else FieldDescriptorWrapper(
                descriptor=model_class._meta.get_field(field_name),
                annotation=annotation,
            )
        )
    except FieldDoesNotExist as e:
        possible_method_or_property = getattr(model_class, field_name, None)

        if isinstance(possible_method_or_property, ComputedRelation):
            field_descriptor = FieldDescriptorWrapper(
                descriptor=possible_method_or_property
            )
        elif possible_method_or_property is not None:
            # TODO: stronger checks here. This could just be a random method with
            # more than the `self` argument. Which would fail at runtime.
            possible_method, is_callable = (
                (possible_method_or_property.fget, False)
                if isinstance(possible_method_or_property, property)
                else (possible_method_or_property, True)
            )
            annotations = get_type_hints(possible_method, localns=resolved_hints)

            field_descriptor = FieldDescriptorWrapper(
                descriptor=ComputedField(
                    name=field_name,
                    annotation=annotations["return"],
                    is_callable=is_callable,
                )
            )
        else:
            raise e

    if len(remaining) == 0:
        return field_descriptor, ()
    elif isinstance(
        field_descriptor.descriptor,
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
            field_descriptor.descriptor.related_model, remaining
        )

        # TODO: Maybe RelatedField replaces all of the above?
        # Consolidate around many_* properties
        # OneToOneRel is a subclass of ManyToOneRel so we need to short circuit.
        is_multiple = (
            not isinstance(field_descriptor.descriptor, models.OneToOneRel)
            and isinstance(
                field_descriptor.descriptor,
                (models.ManyToManyField, models.ManyToOneRel),
            )
        ) or field_descriptor.descriptor.many_to_many is True

        # Note: OneToOneRel, like EmailUser.profile could technically be null, but that usually throws an attribute error or is unlikely.
        # So we don't count it as null.
        is_null = (
            isinstance(
                field_descriptor.descriptor, (models.ForeignKey, ComputedRelation)
            )
            and field_descriptor.descriptor.null is True
        )

        return (
            nested_descriptor,
            ((field_name, is_multiple, is_null), *nested_field_names),
        )

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
    needs_null = []

    for item, is_multiple, is_null in path:
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

                if is_null is True:
                    needs_null.append((item, schema["properties"][item]))
            schema = schema["properties"][item]

    # Should have used recursion. Instead we used dictionary references so we
    # null items this way.
    for item, marked_for_null in needs_null:
        contents = {**marked_for_null}
        marked_for_null.clear()
        marked_for_null.update({"anyOf": [contents, {"type": "null"},]})

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

            field_schema = create_schema(
                field_descriptor.annotation or field_descriptor.descriptor, definitions
            )
            definitions = {**definitions, **field_schema.definitions}

            # Should have used recursion. But instead we have top level null
            # handling here as well.
            if list(reference.keys()) == ["anyOf"]:
                reference = reference["anyOf"][0]

            target_name = (
                field_descriptor.target_name or field_descriptor.descriptor.name
            )
            reference["properties"][target_name] = field_schema.schema
            reference["required"].append(target_name)

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
