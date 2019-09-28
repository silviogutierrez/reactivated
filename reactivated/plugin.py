from typing import Callable, List, Optional
from typing import Type as TypingType
from typing import TypeVar

from mypy.mro import MroError, calculate_mro
from mypy.nodes import (
    ARG_POS,
    GDEF,
    Argument,
    Block,
    ClassDef,
    SymbolTable,
    SymbolTableNode,
    TypeInfo,
    Var,
)
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
    def get_type_analyze_hook(
        self, fullname: str
    ) -> Optional[Callable[[AnalyzeTypeContext], Type]]:
        if fullname == "reactivated.pick.Pick":
            return analyze_pick

        return None

    def get_class_decorator_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname == "reactivated.templates.template":
            return analyze_template

        return None

    def get_dynamic_class_hook(self, fullname: str) -> "CB[DynamicClassDefContext]":
        if fullname == "django.forms.models.modelformset_factory":
            return analyze_modelformset_factory
        return None


def analyze_modelformset_factory(ctx: DynamicClassDefContext) -> None:
    form_set_class = ctx.api.lookup_fully_qualified_or_none(
        "django.forms.formsets.BaseFormSet"
    )
    assert form_set_class is not None

    form_set_class_instance = Instance(form_set_class.node, [])  # type: ignore

    cls_bases: List[Instance] = [form_set_class_instance]
    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)

    info = TypeInfo(SymbolTable(), class_def, ctx.api.cur_mod_id)
    class_def.info = info
    obj = ctx.api.builtin_type("builtins.object")
    info.bases = cls_bases or [obj]
    try:
        calculate_mro(info)
    except MroError:
        ctx.api.fail("Not able to calculate MRO for declarative base", ctx.call)
        info.bases = [obj]
        info.fallback_to_any = True

    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))


def analyze_pick(ctx: AnalyzeTypeContext) -> Type:
    return ctx.api.visit_unbound_type(ctx.type.args[0])  # type: ignore


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
        variable=Var("request", Instance(http_request.node, [])),  # type: ignore
        type_annotation=Instance(http_request.node, []),  # type: ignore
        initializer=None,
        kind=ARG_POS,
    )

    add_method(
        ctx,
        "render",
        args=[request_arg],
        return_type=Instance(template_response.node, []),  # type: ignore
    )


def plugin(version: str) -> TypingType[Plugin]:
    return ReactivatedPlugin
