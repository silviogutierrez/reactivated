from typing import Any

import simplejson
from jsonschema import validate  # type: ignore[import-untyped]


def convert_to_json_and_validate(instance: Any, schema: Any) -> None:
    def merge_all_of(json_input: Any) -> Any:
        if isinstance(json_input, dict):
            if (allOf := json_input.get("allOf")) and json_input.get(
                "_reactivated_testing_merge"
            ) is True:
                merged: Any = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                }
                for to_merge in allOf:
                    dereferenced = (
                        schema.definitions[to_merge["$ref"].replace("#/$defs/", "")]
                        if "$ref" in to_merge
                        else to_merge
                    )
                    merged["properties"].update(dereferenced["properties"])
                    merged["required"].extend(dereferenced["required"])
                return merged

            return {key: merge_all_of(value) for key, value in json_input.items()}
        elif isinstance(json_input, list):
            return [merge_all_of(value) for value in json_input]
        return json_input

    merged_definitions = merge_all_of(schema.definitions)
    converted = simplejson.loads(simplejson.dumps(instance))

    # In case the actual schema we're checking itself needs merging.
    merged_schema = merge_all_of(schema.schema)

    validate(instance=converted, schema={"$defs": merged_definitions, **merged_schema})
