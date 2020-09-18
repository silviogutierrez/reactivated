from typing import Callable, List, Optional
from typing import Type as TypingType
from typing import TypeVar

from mypy.mro import MroError, calculate_mro
from mypy.nodes import (
    AssignmentStmt,
    ARG_POS,
    GDEF,
    Argument,
    Block,
    ClassDef,
    Context,
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
from mypy_django_plugin.lib import helpers

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

    def get_dynamic_class_hook(self, fullname: str) -> "CB[DynamicClassDefContext]":
        if fullname == "django.forms.models.modelformset_factory":
            return analyze_modelformset_factory
        return None


def analyze_modelformset_factory(ctx: DynamicClassDefContext) -> None:
    form_set_class = ctx.api.lookup_fully_qualified_or_none(
        "reactivated.stubs.BaseModelFormSet"
    )
    assert form_set_class is not None

    form_set_class_instance = Instance(
        form_set_class.node, []  # type: ignore[arg-type]
    )

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

    api = ctx.api
    model_classdef = ctx.cls
    current_module = api.modules[model_classdef.info.module_name]
    name = "Foo"

    named_tuple = ctx.api.lookup_fully_qualified_or_none("typing.NamedTuple")

    bases = [Instance(named_tuple.node, [])]

    for possible_form in ctx.cls.defs.body:
        if not isinstance(possible_form, AssignmentStmt):
            continue

        if possible_form.type.type.has_base("django.forms.forms.BaseForm"):
            pass
        elif possible_form.type.type.has_base("django.forms.formsets.BaseFormSet"):
            pass
        else:
            context = Context(line=possible_form.line, column=possible_form.column)

            ctx.api.fail(
                "Only Form and FormSet types are supported", context,
            )

    # breakpoint()
    new_class_info = helpers.add_new_class_for_module(
        current_module,
        name=name,
        bases=bases,
        fields={"composer_form": Instance(template_response.node, [])},
    )

    add_method(
        ctx,
        "is_valid",
        args=[],
        return_type=Instance(
            new_class_info, []  # type: ignore[union-attr, arg-type]
        ),
    )


def plugin(version: str) -> TypingType[Plugin]:
    return ReactivatedPlugin
