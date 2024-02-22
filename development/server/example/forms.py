from typing import Any, Dict

from django import forms
from reactivated.forms import ModelFormSetFactory

from . import models


class ExampleForm(forms.Form):
    char_field = forms.CharField()
    integer_field = forms.IntegerField(help_text="Help for integer field")
    date_field = forms.DateField(widget=forms.SelectDateWidget(years=[2000, 2001]))
    date_time_field = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget,
    )
    choice_field = forms.ChoiceField(
        choices=(
            (1, "One"),
            (2, "Two"),
        )
    )
    boolean_field = forms.BooleanField()
    hidden_field = forms.CharField(widget=forms.HiddenInput)

    def clean(self) -> Dict[str, Any]:
        raise forms.ValidationError(
            "Non-field error",
        )


class Poll(forms.ModelForm[models.Question]):
    class Meta:
        model = models.Question
        fields = ["question_text"]


class Choice(forms.ModelForm[models.Choice]):
    class Meta:
        model = models.Choice
        fields = ["choice_text", "votes"]


class ChoiceFormSet(ModelFormSetFactory[models.Choice, Choice]):
    extra = 0
    min_num = 2
    validate_min = True


class Comment(forms.ModelForm[models.Comment]):
    class Meta:
        model = models.Comment
        fields = ["comment_text"]
