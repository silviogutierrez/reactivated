from typing import Any, Dict, Optional, cast

from django import forms
from django.forms.models import ModelChoiceIterator


class Autocomplete(forms.Select):
    template_name = "reactivated/autocomplete"

    def get_context(
        self, name: str, value: Any, attrs: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        choices = cast(ModelChoiceIterator, self.choices)

        assert choices.queryset is not None
        assert hasattr(
            choices.queryset, "autocomplete"
        ), "Models marked for autocompletion must implement autocomplete(query: str) at the manager level"

        to_field_name = choices.field.to_field_name or "pk"

        # context = forms.Widget.get_context(self, name, value, attrs)
        # self.choices.queryset = self.choices.queryset._clone()[:10]
        # context = super().get_context(name, value, attrs)
        context = forms.Widget.get_context(self, name, value, attrs)
        selected = (
            choices.queryset.filter(**{to_field_name: value}).first() if value else None
        )

        if selected is not None:
            context["widget"]["selected"] = {
                "value": getattr(selected, to_field_name),
                "label": str(selected),
            }
        else:
            context["widget"]["selected"] = None
        return context
