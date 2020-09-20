from django import forms

from sample.server.apps.samples import models


def test_enum_form():
    class EnumForm(forms.ModelForm):
        class Meta:
            fields = ["hemisphere"]
            model = models.Continent

    form = EnumForm({"hemisphere": "Hemisphere.NORTHERN",})

    assert form.is_valid()
