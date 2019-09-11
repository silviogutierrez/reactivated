from typing import Optional, Callable, Type as TypingType

from mypy.plugin import Plugin, AnalyzeTypeContext

from mypy.types import UnionType, TypeType, Type


class ReactivatedPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str) -> Optional[Callable[[AnalyzeTypeContext], Type]]:
        if fullname == "reactivated.pick.Pick":
            return analyze_datum

        return None


def analyze_datum(ctx: AnalyzeTypeContext) -> Type:
    return ctx.api.visit_unbound_type(ctx.type.args[0])  # type: ignore


def plugin(version: str) -> TypingType[Plugin]:
    return ReactivatedPlugin
