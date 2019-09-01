from django import forms

from reactivated.forms import Autocomplete

from . import models


class ComposerForm(forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = "__all__"


class OperaForm(forms.ModelForm):
    class Meta:
        model = models.Opera
        fields = "__all__"
        widgets = {"composer": Autocomplete()}
