from mypy.plugin import Plugin

from mypy.types import UnionType, TypeType


class CustomPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        # if fullname == "reactivated.templates.Template":
        #    return replace_type
        return None

    def get_base_class_hook(self, fullname):
        if fullname == "typing.NamedTuple":
            return analyze_named_tuple
        if fullname == "reactivated.templates.Template":
            return analyze_template
        return None

from mypy.nodes import NamedTupleExpr


def analyze_named_tuple(ctx):
    if ctx.cls.name =="TemplateTest":
        breakpoint()


def analyze_template(ctx):
    defn = ctx.cls
    breakpoint()
    result = ctx.api.named_tuple_analyzer.check_namedtuple_classdef(defn)
    items, types, default_items = result

    info = ctx.api.named_tuple_analyzer.build_namedtuple_typeinfo(
             defn.name, items, types, default_items, defn.line)
    defn.info = info

    breakpoint()
    defn.analyzed = NamedTupleExpr(info, is_typed=True)
    defn.analyzed.line = defn.line
    defn.analyzed.column = defn.column
    # breakpoint()
    return

    breakpoint()
    foo = TypeType(ctx.api.named_type("typing.NamedTuple"))
    print(foo)
    return foo

    """
    return UnionType.make_simplified_union(
        [
            # ctx.api.named_type("typing.NamedTuple"),
            # ctx.api.named_type("builtins.str"),
        ]
    )
    """


def plugin(version: str):
    return CustomPlugin
