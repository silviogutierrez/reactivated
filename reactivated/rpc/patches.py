from __future__ import annotations

import enum
from typing import Any

from pydantic._internal._generate_schema import GenerateSchema
from pydantic_core import core_schema

_original_enum_schema = GenerateSchema._enum_schema


def _is_pick_type(t: Any) -> bool:
    # Lazy import to avoid a circular dependency — patches.py loads before
    # core.py, but these helpers only run during model construction.
    from .core import Pick, PickAsDict

    if not isinstance(t, type):
        return False
    if issubclass(t, Pick):
        return True
    # TypedDict doesn't support issubclass; check bases by identity.
    return PickAsDict in getattr(t, "__orig_bases__", ())


def _is_app_enum(t: type[enum.Enum]) -> bool:
    # An enum DEFINED in an installed Django app speaks member names on every
    # wire — including as a bare RPC-output arm or a Literal[member] tag built
    # OUTSIDE any Pick context, where the stack check alone would fall through
    # to pydantic's default VALUE serialization (one wire format for pick
    # fields, another for direct returns). Ownership decides instead, with
    # nothing to remember (export() is for the client's type + value map,
    # never a serialization prerequisite). SDK enums (e.g. google-genai) never
    # live in app modules and keep pydantic's default handling.
    from .utils import module_name_to_app_name

    return module_name_to_app_name(t.__module__) is not None


# Pydantic 2.10+ deprecated schema_generator and 2.12 ignores it entirely.
# Monkey-patch GenerateSchema._enum_schema so enums validate/serialize by
# member NAME (e.g. "FOO") instead of by value (e.g. "Foo").
# Scoped to Pick subclasses only so third-party pydantic models (e.g.
# google-genai SDK) use pydantic's default enum handling.
def _enum_schema_by_name(
    self: GenerateSchema, enum_type: type[enum.Enum]
) -> core_schema.CoreSchema:
    is_pick_context = any(_is_pick_type(t) for t in self.model_type_stack._stack)

    if not is_pick_context and not _is_app_enum(enum_type):
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
    original = _original_literal_schema(self, literal_type)

    expected = original.get("expected", [])
    enum_members = [v for v in expected if isinstance(v, enum.Enum)]

    is_pick_context = any(_is_pick_type(t) for t in self.model_type_stack._stack)

    # Outside a Pick context, only app-owned enum members coerce by name —
    # mirroring _enum_schema_by_name, so a bare `-> Literal[AppEnum.A, ...]`
    # return (and an app-enum Literal used as a union discriminant) speaks
    # member names on the wire just like a bare enum return. A pure string/int
    # Literal, or one over SDK enums, keeps pydantic's default handling.
    if not is_pick_context and not any(_is_app_enum(type(m)) for m in enum_members):
        return original

    # Only coerce when the literal actually contains enum members.
    if not enum_members:
        return original

    name_to_member = {m.name: m for m in enum_members}

    # Re-key the literal over member NAMES so validation input, json
    # serialization, AND the emitted JSON schema all speak the wire format
    # ("MEMBER"), matching _enum_schema_by_name — the validated python value
    # remains the enum member itself. Without this, Literal[Enum.MEMBER]
    # validates "MEMBER" but dumps (and advertises in generated TypeScript)
    # the enum's *value*, so a model cannot round-trip its own model_dump and
    # the client types lie whenever a member's name differs from its value.
    renamed = [v.name if isinstance(v, enum.Enum) else v for v in expected]

    # An AFTER validator over a heterogeneous literal, not a wrap: pydantic's
    # discriminated-union builder must statically read each arm's tag values
    # out of the discriminator field's core schema, and it can see through
    # function-after ("after validators don't affect the discriminator
    # values") but hard-refuses function-wrap/before/plain. The old wrap made
    # Literal[Enum.MEMBER] unusable as a union discriminant. The literal
    # accepts both spellings — wire NAMES (JSON input) and the members
    # themselves (direct Python construction) — so the inferred tag set
    # covers both, and the after step normalizes names to members.
    def coerce_enum_literal(value: Any) -> Any:
        if isinstance(value, enum.Enum):
            return value
        return name_to_member.get(value, value)

    def serialize(value: Any, info: core_schema.SerializationInfo) -> Any:
        if info.mode == "json" and isinstance(value, enum.Enum):
            return value.name
        return value

    result = core_schema.no_info_after_validator_function(
        coerce_enum_literal,
        core_schema.literal_schema(renamed + enum_members),
        serialization=core_schema.plain_serializer_function_ser_schema(
            serialize, info_arg=True
        ),
    )
    # The heterogeneous literal would leak member VALUES into the JSON
    # schema (and from there into generated TypeScript); advertise the wire
    # NAMES only, same as the wire itself.
    result["metadata"] = {
        "pydantic_js_functions": [
            lambda _core, handler: handler(core_schema.literal_schema(renamed))
        ]
    }
    return result


GenerateSchema._literal_schema = _literal_schema_with_enum_coercion  # type: ignore[method-assign]
