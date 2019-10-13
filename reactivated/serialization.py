from typing import Any, Mapping, NamedTuple, Sequence, Union

from .stubs import _GenericAlias

Schema = Mapping[Any, Any]

Definitions = Mapping[str, Schema]


class Thing(NamedTuple):
    schema: Schema
    definitions: Definitions


def generic_alias_schema(Type: _GenericAlias, definitions: Definitions) -> Thing:
    subschemas: Sequence[Schema]

    if Type.__origin__ == tuple:
        *tuple_args, last_arg = Type.__args__

        if last_arg is Ellipsis:
            items_schema = create_schema(tuple_args[0], definitions)

            return Thing(
                schema={"type": "array", "items": items_schema.schema},
                definitions=items_schema.definitions,
            )

        subschemas = ()

        for subtype in Type.__args__:
            subschema = create_schema(subtype, definitions=definitions)
            subschemas = (*subschemas, subschema.schema)
            definitions = {**definitions, **subschema.definitions}

        return Thing(
            schema={"type": "array", "items": subschemas}, definitions=definitions
        )
    elif Type.__origin__ == Union:
        subschemas = ()

        for subtype in Type.__args__:
            subschema = create_schema(subtype, definitions=definitions)
            subschemas = (*subschemas, subschema.schema)
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
            schema={"type": "object", "additionalProperties": subschema.schema},
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
        definitions = {**field_schema.definitions}

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


def create_schema(Type: Any, definitions: Definitions) -> Thing:
    if isinstance(Type, _GenericAlias):
        return generic_alias_schema(Type, definitions)
    elif Type == Any:
        return Thing(schema={}, definitions=definitions)
    elif issubclass(Type, tuple) and callable(getattr(Type, "_asdict", None)):
        return named_tuple_schema(Type, definitions)
    elif issubclass(Type, bool):
        return Thing(schema={"type": "boolean"}, definitions={})
    elif issubclass(Type, int):
        return Thing(schema={"type": "number"}, definitions={})
    elif issubclass(Type, str):
        return Thing(schema={"type": "string"}, definitions={})
    elif callable(getattr(Type, "get_json_schema", None)):
        return Thing(schema=Type.get_json_schema(), definitions=definitions)
    assert False, f"Unsupported type {Type}"
