from django import forms


class SampleForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
