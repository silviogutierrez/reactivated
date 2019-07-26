from django import forms


class Autocomplete(forms.Select):
    template_name = 'reactivated/autocomplete'

    def get_context(self, name, value, attrs):
        # context = forms.Widget.get_context(self, name, value, attrs)
        self.choices.queryset = self.choices.queryset._clone()[:10]
        return super().get_context(name, value, attrs)
