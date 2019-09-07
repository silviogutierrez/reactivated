from mypy.plugin import Plugin

from mypy.types import UnionType


class CustomPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        # print(fullname)
        if fullname == 'types.Bar':
            return analyze_some_name

        return None

    def get_function_hook(self, fullname: str):
        if fullname == 'types.ssr':
            return analyze_ssr

        return None


def analyze_some_name(ctx):
    return UnionType.make_simplified_union([ctx.api.named_type('types.Bar'), ctx.api.named_type('builtins.int'), ctx.api.named_type('builtins.str')])
    # foo = ctx.api.named_type('builtins.int')
    # foo = ctx.api.named_type('builtins.int')
    # breakpoint()
    # return foo


def analyze_ssr(ctx):
    arg_type = ctx.arg_types[0][0]
    print(arg_type.arg_types)
    print(arg_type.arg_kinds)
    print(arg_type.arg_names)
    print(arg_type.ret_type)
    # print(arg_type.variables)
    print(ctx.api.named_type('builtins.int'), arg_type.arg_types[0])

    # breakpoint()

    try:
        del ctx.api.errors.error_info_map['types.py'][1]
    except Exception:
        pass

    return ctx.default_return_type.copy_modified(
        arg_types=[],
        arg_kinds=[],
        arg_names=[],
        ret_type=ctx.api.named_type('builtins.int'),
    )
    # return ctx.api.named_type('types.ssr')


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return CustomPlugin
