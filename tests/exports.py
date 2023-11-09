import enum
from typing import NamedTuple

from django import forms

from reactivated import export, serialization
from reactivated.apps import get_values
from reactivated.serialization.registry import value_registry


class SimpleEnum(enum.Enum):
    FIRST = "First"
    SECOND = "Second"


class ComplexMember(NamedTuple):
    ranking: int


class ComplexEnum(enum.Enum):
    FIRST = ComplexMember(ranking=1)
    SECOND = ComplexMember(ranking=2)


class SimpleForm(forms.Form):
    some_field = forms.CharField()


def test_export_registry():
    FOO = 1
    BAR = 2

    export(FOO)

    export(BAR)

    assert value_registry["FOO"] == (1, "primitive")
    assert value_registry["BAR"] == (2, "primitive")


def test_export_complex_types():
    value_registry["SimpleForm"] = [SimpleForm, False]
    generated_schema = serialization.create_schema(SimpleForm, {})
    assert get_values()["SimpleForm"] == serialization.serialize(
        SimpleForm, generated_schema
    )

    del value_registry["SimpleForm"]


def test_export_enum():
    export(SimpleEnum)
    # generated_schema = serialization.create_schema(Type[SimpleEnum], {})
    assert get_values()["tests.exports.SimpleEnum"] == {
        "FIRST": "First",
        "SECOND": "Second",
    }

    export(ComplexEnum)
    assert get_values()["tests.exports.ComplexEnum"] == {
        "FIRST": {"ranking": 1},
        "SECOND": {"ranking": 2},
    }
