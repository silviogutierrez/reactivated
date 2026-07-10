import enum
from typing import Literal

import pytest

from reactivated.pick import export
from reactivated.rpc.core import (
    exported_values_registry,
    manually_exported_registry,
    value_registry,
)


class Flavor(enum.Enum):
    VANILLA = "Vanilla"
    CHOCOLATE = "Chocolate"


Snap = Literal["Allowed", "Values"]

SNAP_LIST: list[Snap] = ["Allowed", "Values"]

UNANNOTATED_MAP = {"a": 1, "b": 2}


def test_enum_always_exports_type_and_values():
    export(Flavor, name="tests.Flavor")
    key = next(k for k in value_registry if k.endswith(".Flavor"))
    assert value_registry[key] is Flavor
    assert manually_exported_registry[key] is Flavor


def test_literal_alias_is_type_only():
    export(Snap, name="tests.Snap")
    key = next(k for k in manually_exported_registry if k.endswith(".Snap"))
    assert key not in exported_values_registry


def test_annotated_value_records_its_annotation():
    export(SNAP_LIST, name="tests.SNAP_LIST")
    key = next(k for k in exported_values_registry if k.endswith(".SNAP_LIST"))
    value, annotation = exported_values_registry[key]
    assert value == ["Allowed", "Values"]
    assert annotation == list[Snap]


def test_unannotated_value_has_no_annotation():
    export(UNANNOTATED_MAP, name="tests.UNANNOTATED_MAP")
    key = next(k for k in exported_values_registry if k.endswith(".UNANNOTATED_MAP"))
    value, annotation = exported_values_registry[key]
    assert value == {"a": 1, "b": 2}
    assert annotation is None


def test_non_primitive_is_a_boot_error():
    class Sneaky:
        pass

    with pytest.raises(TypeError, match="not a\n?.*primitive|primitive"):
        export({"thing": Sneaky()}, name="SNEAKY")


def test_duplicate_name_is_a_boot_error():
    export(3, name="THE_NUMBER")
    with pytest.raises(TypeError, match="duplicate"):
        export(4, name="THE_NUMBER")
