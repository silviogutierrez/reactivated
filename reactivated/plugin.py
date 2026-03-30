from collections.abc import Callable
from typing import Type as TypingType
from typing import TypeVar

from mypy.nodes import (
    ARG_POS,
    MDEF,
    Argument,
    Block,
    FuncDef,
    PassStmt,
    SymbolTableNode,
    Var,
)
from mypy.plugin import AnalyzeTypeContext, ClassDefContext, Plugin
from mypy.semanal_shared import set_callable_name
from mypy.types import CallableType, Instance, Type
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name

T = TypeVar("T")


class ReactivatedPlugin(Plugin):
    def get_type_analyze_hook(
        self, fullname: str
    ) -> Callable[[AnalyzeTypeContext], Type] | None:
        if fullname == "reactivated.pick.Pick":
            return analyze_pick

        return None

    def get_class_decorator_hook_2(
        self, fullname: str
    ) -> Callable[[ClassDefContext], bool] | None:
        if fullname in [
            "reactivated.templates.template",
            "reactivated.templates.interface",
        ]:
            return analyze_template

        return None


def analyze_pick(ctx: AnalyzeTypeContext) -> Type:
    return ctx.api.visit_unbound_type(  # type: ignore[no-any-return, attr-defined]
        ctx.type.args[0]
    )


def analyze_template(ctx: ClassDefContext) -> bool:
    info = ctx.cls.info

    # Idempotency: this hook may be called multiple times per class.
    # If render was already added by this plugin, skip.
    if "render" in info.names:
        sym = info.names["render"]
        if sym.plugin_generated:
            return True

    template_response = ctx.api.lookup_fully_qualified_or_none(
        "django.template.response.TemplateResponse"
    )

    if template_response is None or template_response.node is None:
        return False

    http_request = ctx.api.lookup_fully_qualified_or_none("django.http.HttpRequest")

    if http_request is None or http_request.node is None:
        return False

    # Build the render(request: HttpRequest) -> TemplateResponse method.
    #
    # We add ONLY to info.names, not to cls.defn.defs.body. The old approach
    # of using add_method() appends a FuncDef to the class body, which
    # corrupts NamedTuple classes: mypy rebuilds NamedTuple info from the body
    # on each semantic analysis pass, and the extra FuncDef causes the
    # NamedTuple fields to be lost, triggering infinite re-analysis.
    self_type = fill_typevars(info)
    request_type = Instance(http_request.node, [])  # type: ignore[arg-type]
    return_type = Instance(template_response.node, [])  # type: ignore[arg-type]
    function_type = ctx.api.named_type("builtins.function", [])

    args = [
        Argument(Var("self"), self_type, None, ARG_POS),
        Argument(
            variable=Var("request", request_type),
            type_annotation=request_type,
            initializer=None,
            kind=ARG_POS,
        ),
    ]

    arg_types = [a.type_annotation for a in args]
    arg_names = [a.variable.name for a in args]
    arg_kinds = [a.kind for a in args]

    signature = CallableType(
        arg_types,  # type: ignore[arg-type]
        arg_kinds,
        arg_names,
        return_type,
        function_type,
    )

    func = FuncDef("render", args, Block([PassStmt()]))
    func.info = info
    func.type = set_callable_name(signature, func)
    func._fullname = info.fullname + ".render"
    func.line = info.line

    sym = SymbolTableNode(MDEF, func)
    sym.plugin_generated = True

    # If there's an existing "render" entry, rename it to avoid conflict
    if "render" in info.names:
        r_name = get_unique_redefinition_name("render", info.names)
        info.names[r_name] = info.names["render"]

    info.names["render"] = sym

    return True


def plugin(version: str) -> TypingType[Plugin]:
    return ReactivatedPlugin
