from django import forms

from reactivated.forms import Autocomplete
from sample.server.apps.samples import models


class ComposerForm(forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = "__all__"


ComposerFormSet = forms.modelformset_factory(
    model=models.Composer, form=ComposerForm, extra=0, min_num=1, validate_min=True
)


class OperaForm(forms.ModelForm):
    class Meta:
        model = models.Opera
        fields = "__all__"
        widgets = {"composer": Autocomplete()}


OperaFormSet = forms.modelformset_factory(
    model=models.Opera, form=OperaForm, extra=0, min_num=1, validate_min=True
)
