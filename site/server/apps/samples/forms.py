from django import forms

from . import models


class ComposerForm(forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = '__all__'
