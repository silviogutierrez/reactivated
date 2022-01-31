from django import forms

from . import models


class StoryboardForm(forms.Form):
    char_field = forms.CharField()
    integer_field = forms.IntegerField()
    date_field = forms.DateField(widget=forms.SelectDateWidget(years=[2000, 2001]))
    date_time_field = forms.DateTimeField(widget=forms.SplitDateTimeWidget,)
    choice_field = forms.ChoiceField(choices=((1, "One"), (2, "Two"),))
    boolean_field = forms.BooleanField()


class Poll(forms.ModelForm):
    class Meta:
        model = models.Question
        fields = ["question_text"]


class Choice(forms.ModelForm):
    class Meta:
        model = models.Choice
        fields = ["choice_text"]


ChoiceFormSet = forms.modelformset_factory(
    model=models.Choice, form=Choice, extra=3, min_num=1, validate_min=True
)
