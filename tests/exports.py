from django import forms

from reactivated import export, serialization
from reactivated.apps import get_values
from reactivated.serialization.registry import value_registry
import enum


class SimpleEnum(enum.Enum):
    value: str

    FIRST = "First"
    SECOND = "Second"


class SimpleForm(forms.Form):
    some_field = forms.CharField()


def test_export_registry():
    FOO = 1
    BAR = 2

    export(FOO)

    export(BAR)

    assert value_registry["FOO"] == (1, True)
    assert value_registry["BAR"] == (2, True)


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

    print(get_values())
    assert False
    return


    del value_registry["SimpleForm"]
