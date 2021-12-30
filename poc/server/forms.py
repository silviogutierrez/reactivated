from django import forms


class StoryboardForm(forms.Form):
    char_field = forms.CharField()
    integer_field = forms.IntegerField()
    date_field = forms.DateField(widget=forms.SelectDateWidget)
    date_time_field = forms.DateTimeField(widget=forms.SplitDateTimeWidget,)
    choice_field = forms.ChoiceField(choices=((1, "One"), (2, "Two"),))
    boolean_field = forms.BooleanField()
