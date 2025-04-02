from . import registry


@registry.register(int)
class Int:
    @classmethod
    def get_json_schema(
        Proxy: type["Int"],
        instance: int,
        definitions: registry.Definitions,
    ) -> registry.Thing:
        return registry.Thing(schema={"type": "number"}, definitions=definitions)


@registry.register(bool)
class Bool:
    @classmethod
    def get_json_schema(
        Proxy: type["Bool"],
        instance: bool,
        definitions: registry.Definitions,
    ) -> registry.Thing:
        return registry.Thing(schema={"type": "boolean"}, definitions=definitions)


@registry.register(float)
class Float:
    @classmethod
    def get_json_schema(
        Proxy: type["Float"],
        instance: float,
        definitions: registry.Definitions,
    ) -> registry.Thing:
        return registry.Thing(schema={"type": "number"}, definitions=definitions)


@registry.register(str)
class String:
    @classmethod
    def get_json_schema(
        Proxy: type["String"],
        instance: str,
        definitions: registry.Definitions,
    ) -> registry.Thing:
        return registry.Thing(schema={"type": "string"}, definitions=definitions)
