from django import forms


class Autocomplete(forms.Select):
    template_name = 'reactivated/autocomplete'
