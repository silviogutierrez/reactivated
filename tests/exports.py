from reactivated import export
from reactivated.serialization.registry import value_registry


def test_export_registry():
    FOO = 1
    BAR = 2

    export(FOO)

    export(BAR)

    assert value_registry["FOO"] == 1
    assert value_registry["BAR"] == 2
