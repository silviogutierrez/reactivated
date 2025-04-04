from __future__ import annotations

import hashlib
import inspect
from collections.abc import Sequence
from types import ModuleType
from typing import Any, Literal, NamedTuple, get_type_hints

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields.reverse_related import ForeignObjectRel

from .models import ComputedRelation
from .serialization import ComputedField, FieldDescriptor, create_schema
from .serialization.registry import (
    DefaultModelsType,
    Definitions,
    JSONSchema,
    Thing,
    global_types,
)
from .stubs import _LiteralGenericAlias

FieldSegment = tuple[str, bool, bool]


class FieldDescriptorWrapper(NamedTuple):
    descriptor: FieldDescriptor
    target_name: str | None = None
    annotation: Any | None = None


def get_field_descriptor(
    pick_name: str, model_class: type[models.Model], field_chain: list[str]
) -> tuple[FieldDescriptorWrapper, Sequence[FieldSegment]]:
    field_name, *remaining = field_chain

    resolved_hints = (
        model_class.resolve_type_hints()
        if hasattr(model_class, "resolve_type_hints")
        else {}
    )

    try:
        overrides = get_type_hints(model_class, localns=resolved_hints)
        annotation = overrides.get(field_name, None)

        field_descriptor = (
            FieldDescriptorWrapper(
                descriptor=model_class._meta.pk, annotation=annotation, target_name="pk"
            )
            if field_name == "pk"
            else FieldDescriptorWrapper(
                descriptor=model_class._meta.get_field(field_name),  # type: ignore[arg-type]
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

    if isinstance(
        field_descriptor.descriptor,
        (
            models.ForeignKey,
            models.OneToOneField,
            models.ManyToManyField,
            models.ManyToOneRel,
            ComputedRelation,
            # TODO: Maybe RelatedField replaces all of the above?
            models.fields.related.RelatedField,
        ),
    ):
        if len(remaining) == 0:
            if isinstance(field_descriptor.descriptor, ForeignObjectRel):
                assert (
                    False
                ), f"You cannot Pick reverse relationships. Specify which fields from {field_name} you want, such as {field_name}.example_field"

            if (
                isinstance(field_descriptor.descriptor, (models.ForeignKey))
                and field_name == field_descriptor.descriptor.attname
            ):
                copy = field_descriptor.descriptor.foreign_related_fields[0].__class__(
                    null=field_descriptor.descriptor.null
                )

                return (
                    FieldDescriptorWrapper(
                        descriptor=copy,
                        target_name=field_name,
                        annotation=None,
                    ),
                    (),
                )

            assert (
                False
            ), f"Do not specify related fields directly for model {model_class} in {pick_name}. Use {field_name}_id if you just want the reference or {field_name}.subfield if you want fields inside the related model"

        nested_descriptor, nested_field_names = get_field_descriptor(
            pick_name, field_descriptor.annotation or field_descriptor.descriptor.related_model, remaining  # type: ignore[arg-type]
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

        # Note: OneToOneRel, like EmailUser.profile could technically be null.
        # In Django world, it throws an exception.  But when serializing, we
        # always assume null unless manually annotated say, for user profile
        # because we always know it's not null.
        is_null = (
            isinstance(field_descriptor.descriptor, models.OneToOneRel)
            and field_descriptor.annotation is None
        ) or (
            isinstance(
                field_descriptor.descriptor, (models.ForeignKey, ComputedRelation)
            )
            and field_descriptor.descriptor.null is True
        )

        return (
            nested_descriptor,
            ((field_name, is_multiple, is_null), *nested_field_names),
        )
    elif len(remaining) == 0:
        return field_descriptor, ()

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


def build_nested_schema(
    schema_or_null: JSONSchema, path: Sequence[FieldSegment]
) -> JSONSchema:
    needs_null = []

    for item, is_multiple, is_null in path:
        # Because we mark null and convet to anyOf on each path, doing nested
        # nullable paths Like foo?.bar?.name and foo?.bar?.id will fail if we
        # don't first peek ahead into the anyOf. Then it'll be remarked as
        # needs_null anyway. It's messy but we should use recursion instead of
        # do this cleanly.
        # See test_nested_null_foreign_keys
        schema = (
            schema_or_null["anyOf"][0] if "anyOf" in schema_or_null else schema_or_null
        )

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
            schema_or_null = schema["properties"][item]["items"]
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
            schema_or_null = schema["properties"][item]

    # Should have used recursion. Instead we used dictionary references so we
    # null items this way.
    for item, marked_for_null in needs_null:
        contents = {**marked_for_null}
        marked_for_null.clear()
        marked_for_null.update(
            {
                "anyOf": [
                    contents,
                    {"type": "null"},
                ]
            }
        )

    return schema_or_null


class BasePickHolder:
    model_class: type[models.Model]
    module: ModuleType
    fields: list[str] = []

    @classmethod
    def get_name(cls: type[BasePickHolder]) -> str | None:
        pick_name: str | None = None

        for var_name, var_val in inspect.getmembers(cls.module):
            if (
                isinstance(var_val, type)
                and issubclass(var_val, BasePickHolder)
                and var_val.module == cls.module
                and var_val.fields == cls.fields
                and var_val.model_class is cls.model_class
            ):
                pick_name = var_name

        if pick_name is None:
            return None

        for app_config in apps.get_app_configs():
            if app_config.name in cls.module.__name__:
                relative_module = cls.module.__name__.replace(f"{app_config.name}.", "")
                return f"{app_config.label}.{relative_module}.{pick_name}"

        return None

    @classmethod
    def get_auto_name(cls: type[BasePickHolder]) -> str:
        model_name = f"{cls.model_class.__module__}.{cls.model_class.__qualname__}"
        fields = "_".join(sorted(cls.fields))
        unhashed = f"{model_name}{fields}"
        hash = hashlib.sha1(unhashed.encode("UTF-8")).hexdigest()[:10]
        return f"{cls.model_class.__qualname__}_{hash}"

    @classmethod
    def get_json_schema(cls: type[BasePickHolder], definitions: Definitions) -> Thing:
        explicit_name = cls.get_name()

        definition_name = explicit_name or cls.get_auto_name()
        ref = {"$ref": f"#/$defs/{definition_name}"}

        if definition_name in definitions:
            return Thing(schema=ref, definitions=definitions)

        if global_types["models"] is DefaultModelsType:
            global_types["models"] = {
                "type": "object",
                "additionalProperties": False,
                "required": [],
                "properties": {},
            }

        if explicit_name is not None:
            global_types["models"] = {
                **global_types["models"],
                "required": [*global_types["models"]["required"], definition_name],
                "properties": {
                    **global_types["models"]["properties"],
                    definition_name: ref,
                },
            }

        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
            "required": [],
            "title": definition_name,
        }

        for field_name in cls.fields:
            field_descriptor, path = get_field_descriptor(
                definition_name, cls.model_class, field_name.split(".")
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

        return Thing(
            schema=ref,
            definitions={
                **definitions,
                definition_name: schema,
            },
        )


class Pick:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        meta_model, *meta_fields = item

        if type(meta_model) is _LiteralGenericAlias:
            related_field = meta_model.__args__[0]
            nested_fields = []

            for nested_field in meta_fields[0].fields:
                nested_fields.append(f"{related_field}.{nested_field}")
            return nested_fields

        flattened_fields: list[str] = []

        for field_or_literal in meta_fields:
            if isinstance(field_or_literal, str):
                flattened_fields.append(field_or_literal)
            elif isinstance(field_or_literal, list):
                flattened_fields.extend(field_or_literal)
            elif field_or_literal.__origin__ == Literal:
                flattened_fields.extend(field_or_literal.__args__)
            else:
                assert False, f"Unsupported pick property {field_or_literal}"

        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])

        class PickHolder(BasePickHolder):
            model_class = meta_model
            fields = flattened_fields
            module = mod  # type: ignore[assignment]

        return PickHolder
