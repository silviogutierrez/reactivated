from mypy.plugin import Plugin

from mypy.types import UnionType


class CustomPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        # print(fullname)
        if fullname == 'types.Bar':
            return analyze_some_name

        return None

    def get_function_hook(self, fullname: str):
        if False and fullname == 'types.ssr':
            return analyze_ssr

        return None


def analyze_some_name(ctx):
    return UnionType.make_simplified_union([ctx.api.named_type('types.Bar'), ctx.api.named_type('builtins.int'), ctx.api.named_type('builtins.str')])
    # foo = ctx.api.named_type('builtins.int')
    # foo = ctx.api.named_type('builtins.int')
    # breakpoint()
    # return foo


def analyze_ssr(ctx):
    # breakpoint()
    return ctx.api.named_type('types.ssr')


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return CustomPlugin
