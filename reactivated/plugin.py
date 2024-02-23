from typing import Callable, Optional
from typing import Type as TypingType
from typing import TypeVar

from mypy.nodes import ARG_POS, Argument, Var
from mypy.plugin import AnalyzeTypeContext, ClassDefContext, Plugin
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
