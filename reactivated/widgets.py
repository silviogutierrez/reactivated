from django import forms


class Autocomplete(forms.Select):
    template_name = 'reactivated/autocomplete'

    def get_context(self, name, value, attrs):
        to_field_name = self.choices.field.to_field_name or 'pk'

        # context = forms.Widget.get_context(self, name, value, attrs)
        # self.choices.queryset = self.choices.queryset._clone()[:10]
        # context = super().get_context(name, value, attrs)
        context = forms.Widget.get_context(self, name, value, attrs)
        selected = self.choices.queryset.filter(**{to_field_name: value}).first() if value else None

        if selected is not None:
            context['widget']['selected'] = {"value": getattr(selected, to_field_name), "label": str(selected)}
        else:
            context['widget']['selected'] = None
        return context
