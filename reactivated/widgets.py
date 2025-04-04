from typing import Any, Literal, NamedTuple, cast

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import ModelChoiceIterator

from .serialization.registry import register
from .serialization.widgets import BaseWidget


class Autocomplete(forms.Select):
    template_name: Literal["reactivated/autocomplete"] = "reactivated/autocomplete"

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
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
        try:
            selected = choices.field.to_python(value)
        except ValidationError:
            selected = None

        if selected is not None:
            context["widget"]["selected"] = {
                "value": getattr(selected, to_field_name),
                "label": str(selected),
            }
        else:
            context["widget"]["selected"] = None

        return context


class AutocompleteSelected(NamedTuple):
    value: str | int
    label: str


@register(Autocomplete)
class AutocompleteType(BaseWidget):
    value: list[str]  # type: ignore[assignment]
    selected: AutocompleteSelected | None
