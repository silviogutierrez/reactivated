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
        if fullname in [
            "reactivated.templates.template",
            "reactivated.templates.interface",
        ]:
            return analyze_template

        return None

    def get_base_class_hook(self, fullname: str) -> "CB[ClassDefContext]":
        if fullname in ["django.forms.formsets.BaseFormSet"]:
            return analyze_stubs
        return None

    def get_dynamic_class_hook(self, fullname: str) -> "CB[DynamicClassDefContext]":
        if fullname in [
            "django.forms.formsets.formset_factory",
            "django.forms.models.modelformset_factory",
        ]:
            return analyze_formset_factory
        return None


def analyze_stubs(ctx: ClassDefContext) -> None:
    boolean = ctx.api.builtin_type("builtins.bool")

    add_method(
        ctx,
        "is_valid",
        args=[],
        return_type=Instance(boolean.type, []),
    )


already_analyzed = {}


def analyze_formset_factory(ctx: DynamicClassDefContext) -> None:
    class_lookup = (
        "reactivated.stubs.BaseModelFormSet"
        if ctx.call.callee.name == "modelformset_factory"  # type: ignore[attr-defined]
        else "reactivated.stubs.BaseFormSet"
    )
    form_set_class = ctx.api.lookup_fully_qualified_or_none(
        class_lookup,
    )
    assert form_set_class is not None

    form_set_class_instance = Instance(
        form_set_class.node, []  # type: ignore[arg-type]
    )

    cls_bases: List[Instance] = [form_set_class_instance]
    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)

    if class_def.fullname in already_analyzed:
        # Fixes an issue with max iteration counts.
        # In theory add_symbol_table_node should already guard against this but
        # it doesn't.
        return

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

    already_analyzed[class_def.fullname] = True
    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))


def analyze_pick(ctx: AnalyzeTypeContext) -> Type:
    return ctx.api.visit_unbound_type(  # type: ignore[no-any-return, attr-defined]
        ctx.type.args[0]
    )


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
            http_request.node, []  # type: ignore[union-attr, arg-type]
        ),
        initializer=None,
        kind=ARG_POS,
    )

    add_method(
        ctx,
        "render",
        args=[request_arg],
        return_type=Instance(
            template_response.node, []  # type: ignore[union-attr, arg-type]
        ),
    )


def plugin(version: str) -> TypingType[Plugin]:
    return ReactivatedPlugin
