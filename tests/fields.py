import enum

import pytest
from django import forms
from django.apps.registry import Apps
from django.core.exceptions import ValidationError
from django.db.models import Model

from reactivated import constraints, fields
from sample.server.apps.samples import models


class EnumTest(enum.Enum):
    FIRST = "First"
    SECOND = "Second"


def test_enum_form():
    class EnumForm(forms.ModelForm):
        class Meta:
            fields = ["hemisphere"]
            model = models.Continent

    form = EnumForm({"hemisphere": "Hemisphere.NORTHERN"})

    assert form.is_valid()

    form = EnumForm({"hemisphere": "wrong"})
    assert form.is_valid() is False


def test_convert_enum_to_choices():
    assert list(fields.convert_enum_to_choices(EnumTest)) == [
        (EnumTest.FIRST, "First"),
        (EnumTest.SECOND, "Second"),
    ]


def test_parse_enum():
    assert fields.parse_enum(EnumTest, None) is None
    assert fields.parse_enum(EnumTest, "SECOND") is EnumTest.SECOND
    assert fields.parse_enum(EnumTest, "EnumTest.SECOND") is EnumTest.SECOND

    with pytest.raises(ValidationError, match=f"Invalid .* {EnumTest}"):
        fields.parse_enum(EnumTest, "FAKE")


def test_auto_contraint(settings):
    settings.INSTALLED_APPS = ["tests.fields"]
    test_apps = Apps(settings.INSTALLED_APPS)

    class TestModel(Model):
        enum_field = fields.EnumField(enum=EnumTest)

        class Meta:
            apps = test_apps

    constraint = TestModel._meta.constraints[0]
    assert isinstance(constraint, constraints.EnumConstraint)
    assert constraint.members == ["FIRST", "SECOND"]
    assert constraint.field_name == "enum_field"
    assert constraint.name == "fields_testmodel_enum_field_enum"
