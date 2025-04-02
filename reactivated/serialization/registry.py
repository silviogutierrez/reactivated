from collections.abc import Callable, Mapping
from typing import Any, Literal, NamedTuple, TypeVar

from reactivated import types, utils

DefaultWidgetType = {"tsType": 'generated.Types["Widget"]'}
DefaultModelsType = {"type": "null"}

type_registry: dict[str, tuple[Any]] = {}
global_types: dict[str, Any] = {
    "Widget": DefaultWidgetType,
    "models": DefaultModelsType,
}
template_registry: dict[str, tuple[Any]] = {}
interface_registry: dict[str, tuple[Any]] = {}
value_registry: dict[str, tuple[Any, Literal["primitive", "class", "enum"]]] = {}
definitions_registry: dict[Any, Any] = {}
rpc_registry: types.RPCRegistry = {}

PROXIES = utils.ClassLookupDict({})


Override = TypeVar("Override")


def register(proxied: type[object]) -> Callable[[Override], Override]:
    def inner(proxy: Override) -> Override:
        PROXIES[proxied] = proxy
        return proxy

    return inner


PropertySchema = Mapping[str, Any]


Schema = Mapping[Any, Any]


Definitions = Mapping[str, Schema]


JSON = Any


JSONSchema = Any


class Thing(NamedTuple):
    schema: Schema
    definitions: Definitions

    def dereference(self) -> Schema:
        ref = self.schema.get("$ref")

        # Should probably error or Thing should be a subclass for cached
        # schemas that has this property
        if not ref:
            return self.schema

        return self.definitions[ref.replace("#/$defs/", "")]

    def add_property(
        self, name: str, property_schema: PropertySchema, *, optional: bool = False
    ) -> "Thing":
        ref: str | None = self.schema.get("$ref")

        if ref is None:
            assert False, "Can only add properties to ref schemas"

        definition_name = ref.replace("#/$defs/", "")
        dereferenced = self.definitions[definition_name]

        # In case we are replacing a property.
        required = (
            dereferenced["required"]
            if (optional is True or name in dereferenced["required"])
            else [*dereferenced["required"], name]
        )

        return Thing(
            schema=self.schema,
            definitions={
                **self.definitions,
                definition_name: {
                    **dereferenced,
                    "properties": {
                        **dereferenced["properties"],
                        name: property_schema,
                    },
                    "required": required,
                    "additionalProperties": False,
                },
            },
        )
