from __future__ import annotations

import enum
from typing import Any

from pydantic._internal._generate_schema import GenerateSchema
from pydantic_core import core_schema

_original_enum_schema = GenerateSchema._enum_schema


# Pydantic 2.10+ deprecated schema_generator and 2.12 ignores it entirely.
# Monkey-patch GenerateSchema._enum_schema so enums validate/serialize by
# member NAME (e.g. "FOO") instead of by value (e.g. "Foo").
# Scoped to Pick subclasses only so third-party pydantic models (e.g.
# google-genai SDK) use pydantic's default enum handling.
def _enum_schema_by_name(
    self: GenerateSchema, enum_type: type[enum.Enum]
) -> core_schema.CoreSchema:
    # Lazy import to avoid circular dependency — patches.py is loaded before
    # core.py, but this function is only called during model construction.
    from .core import Pick, PickAsDict

    def _is_pick_type(t: Any) -> bool:
        if not isinstance(t, type):
            return False
        if issubclass(t, Pick):
            return True
        # TypedDict doesn't support issubclass; check bases by identity.
        return PickAsDict in getattr(t, "__orig_bases__", ())

    is_pick_context = any(_is_pick_type(t) for t in self.model_type_stack._stack)

    if not is_pick_context:
        return _original_enum_schema(self, enum_type)

    def get_enum(
        value: Any, validate_next: core_schema.ValidatorFunctionWrapHandler
    ) -> Any:
        if isinstance(value, enum_type):
            return value
        name: str = validate_next(value)
        return enum_type[name]

    def serialize(
        value: enum.Enum, info: core_schema.SerializationInfo
    ) -> str | enum.Enum:
        if info.mode == "json":
            return value.name
        return value

    expected = list(enum_type.__members__.keys())
    name_schema = core_schema.literal_schema(expected)

    return core_schema.no_info_wrap_validator_function(
        get_enum,
        name_schema,
        ref=enum_type.__qualname__,
        serialization=core_schema.plain_serializer_function_ser_schema(
            serialize, info_arg=True
        ),
    )


GenerateSchema._enum_schema = _enum_schema_by_name  # type: ignore[method-assign]


# Pydantic's Literal[SomeEnum.MEMBER] requires the exact enum instance during
# validation — it never coerces strings.  This is a problem because JSON input
# always arrives as strings.  Monkey-patch _literal_schema to wrap enum-bearing
# Literal validators with a coercion step that converts member names to instances.
# Scoped to Pick subclasses only, like _enum_schema_by_name above.
_original_literal_schema = GenerateSchema._literal_schema


def _literal_schema_with_enum_coercion(
    self: GenerateSchema, literal_type: Any
) -> core_schema.CoreSchema:
    from .core import Pick, PickAsDict

    def _is_pick_type(t: Any) -> bool:
        if not isinstance(t, type):
            return False
        if issubclass(t, Pick):
            return True
        return PickAsDict in getattr(t, "__orig_bases__", ())

    is_pick_context = any(_is_pick_type(t) for t in self.model_type_stack._stack)

    if not is_pick_context:
        return _original_literal_schema(self, literal_type)

    original = _original_literal_schema(self, literal_type)

    # Only wrap if the literal contains enum members
    expected = original.get("expected", [])
    enum_members = [v for v in expected if isinstance(v, enum.Enum)]
    if not enum_members:
        return original

    name_to_member = {m.name: m for m in enum_members}

    def coerce_enum_literal(
        value: Any, handler: core_schema.ValidatorFunctionWrapHandler
    ) -> Any:
        if isinstance(value, str) and value in name_to_member:
            value = name_to_member[value]
        return handler(value)

    return core_schema.no_info_wrap_validator_function(coerce_enum_literal, original)


GenerateSchema._literal_schema = _literal_schema_with_enum_coercion  # type: ignore[method-assign]
