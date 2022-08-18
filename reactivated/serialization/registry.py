from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from reactivated import utils

DefaultWidgetType = {"tsType": 'generated.Types["Widget"]'}
DefaultModelsType = {"type": "null"}

type_registry: Dict[str, Tuple[Any]] = {}
global_types: Dict[str, Any] = {
    "Widget": DefaultWidgetType,
    "models": DefaultModelsType,
}
template_registry: Dict[str, Tuple[Any]] = {}
interface_registry: Dict[str, Tuple[Any]] = {}
value_registry: Dict[str, Any] = {}
definitions_registry: Dict[Any, Any] = {}

PROXIES = utils.ClassLookupDict({})


Override = TypeVar("Override")


def register(proxied: Type[object]) -> Callable[[Override], Override]:
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

        return self.definitions[ref.replace("#/definitions/", "")]

    def add_property(
        self, name: str, property_schema: PropertySchema, *, optional: bool = False
    ) -> "Thing":
        ref: Optional[str] = self.schema.get("$ref")

        if ref is None:
            assert False, "Can only add properties to ref schemas"

        definition_name = ref.replace("#/definitions/", "")
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
