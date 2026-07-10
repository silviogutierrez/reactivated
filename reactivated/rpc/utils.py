import re
from typing import Any

from django.apps import apps


def module_name_to_app_name(module_name: str) -> str | None:
    for app_config in apps.get_app_configs():
        if module_name == app_config.name:
            return app_config.label
        if module_name.startswith(f"{app_config.name}."):
            relative_module = module_name.replace(f"{app_config.name}.", "")
            return f"{app_config.label}.{relative_module}"

    return None


def flatten_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Flatten a JSON schema by inlining $ref/$defs and converting
    description-encoded enums/consts to native JSON Schema keywords.

    Pydantic's model_json_schema() (and anthropic's transform_schema()) emit
    $defs/$ref for nested types and encode enum/const values in description
    strings. Some consumers (e.g. the Claude Agent SDK's structured output)
    require a fully self-contained schema with no $ref pointers.

    Transformations applied:
    - $ref pointers are replaced with the referenced definition inlined
    - Description strings like ``{enum: ['A', 'B']}`` become ``{"enum": ["A", "B"]}``
    - Description strings like ``{const: VALUE}`` become ``{"const": "VALUE"}``
    - ``title`` and ``format`` keys are stripped (metadata that can confuse
      strict schema validators)
    - ``$defs`` is removed after all references are resolved
    """
    defs = schema.pop("$defs", {})

    def resolve(node: object) -> object:
        if isinstance(node, dict):
            if "$ref" in node:
                ref_name = node["$ref"].rsplit("/", 1)[-1]
                resolved = defs[ref_name].copy()
                for k, v in node.items():
                    if k != "$ref":
                        resolved[k] = v
                return resolve(resolved)

            result = {k: resolve(v) for k, v in node.items()}

            desc = result.get("description", "")
            if isinstance(desc, str):
                enum_match = re.match(r"^\{enum: \[(.+)\]\}$", desc)
                if enum_match:
                    result["enum"] = [
                        v.strip().strip("'\"") for v in enum_match.group(1).split(",")
                    ]
                    del result["description"]

                const_match = re.match(r"^\{const: (.+)\}$", desc)
                if const_match:
                    result["const"] = const_match.group(1)
                    del result["description"]

            result.pop("title", None)
            result.pop("format", None)

            return result
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)  # type: ignore[return-value]
