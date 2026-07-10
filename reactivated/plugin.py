from collections.abc import Callable
from typing import Optional, TypeVar
from typing import Type as TypingType

from mypy.nodes import ARG_POS, GDEF, Argument, PlaceholderNode, SymbolTableNode, Var
from mypy.options import Options
from mypy.plugin import (
    AnalyzeTypeContext,
    ClassDefContext,
    DynamicClassDefContext,
    Plugin,
)
from mypy.plugins.common import add_method
from mypy.types import Instance, Type

T = TypeVar("T")
CB = Optional[Callable[[T], None]]


class ReactivatedPlugin(Plugin):
    def __init__(self, options: Options) -> None:
        super().__init__(options)
        self._placeholder_names: set[str] = set()

    def get_dynamic_class_hook(self, fullname: str) -> "CB[DynamicClassDefContext]":
        # The implementation and its public facade — mypy reports whichever
        # the import chain resolved to.
        if fullname in ("reactivated.rpc.core.pick", "reactivated.pick.pick"):
            return lambda ctx: analyze_rpc_pick(ctx, self._placeholder_names)
        return None


def analyze_pick(ctx: AnalyzeTypeContext) -> Type:
    return ctx.api.visit_unbound_type(  # type: ignore[no-any-return, attr-defined]
        ctx.type.args[0]
    )


def analyze_rpc_pick(ctx: DynamicClassDefContext, placeholder_names: set[str]) -> None:
    current_module = ctx.api.cur_mod_node.fullname  # type: ignore[attr-defined]
    module_name = current_module.replace(".", "_")
    class_name = ctx.name

    definition_name = f"{module_name}_{class_name}"

    model_info = ctx.api.lookup_fully_qualified_or_none(
        f"pick_schema.{definition_name}",
    )

    if model_info is None:
        if not ctx.api.final_iteration:
            key = f"{current_module}.{class_name}"
            if key not in placeholder_names:
                placeholder_names.add(key)
                placeholder = PlaceholderNode(
                    f"{current_module}.{class_name}",
                    ctx.call,
                    ctx.call.line,
                    becomes_typeinfo=True,
                )
                ctx.api.add_symbol_table_node(
                    ctx.name, SymbolTableNode(GDEF, placeholder)
                )
            ctx.api.defer()
        else:
            # Final iteration: can't defer, can't leave a PlaceholderNode
            # (it crashes serialization). Create a fallback TypeInfo so
            # the symbol table gets something serializable.
            object_type = ctx.api.named_type("builtins.object")
            fallback_info = ctx.api.basic_new_typeinfo(
                ctx.name, object_type, ctx.call.line
            )
            fallback_info.fallback_to_any = True
            ctx.api.add_symbol_table_node(
                ctx.name, SymbolTableNode(GDEF, fallback_info)
            )
        return

    ctx.api.add_symbol_table_node(ctx.name, model_info)

    modules = ctx.api.modules

    for mod_name, mod_file in modules.items():
        if mod_name == current_module:
            continue
        if mod_file is not None and class_name in mod_file.names:
            imported_node = mod_file.names[class_name]
            if (
                imported_node.node is not None
                and hasattr(imported_node.node, "fullname")
                and imported_node.node.fullname == f"{current_module}.{class_name}"
            ):
                imported_node.node = model_info.node
                imported_node.kind = model_info.kind


def analyze_template(ctx: ClassDefContext) -> None:
    template_response = ctx.api.lookup_fully_qualified_or_none(
        "django.template.response.TemplateResponse"
    )

    if template_response is None and not ctx.api.final_iteration:
        ctx.api.defer()
        return

    http_request = ctx.api.lookup_fully_qualified_or_none("django.http.HttpRequest")

    if http_request is None and not ctx.api.final_iteration:
        ctx.api.defer()
        return

    request_arg = Argument(
        variable=Var(
            "request",
            Instance(http_request.node, []),  # type: ignore[union-attr, arg-type]
        ),
        type_annotation=Instance(
            http_request.node,  # type: ignore[union-attr, arg-type]
            [],
        ),
        initializer=None,
        kind=ARG_POS,
    )

    add_method(
        ctx,
        "render",
        args=[request_arg],
        return_type=Instance(
            template_response.node,  # type: ignore[union-attr, arg-type]
            [],
        ),
    )


def plugin(version: str) -> TypingType[Plugin]:
    return ReactivatedPlugin
