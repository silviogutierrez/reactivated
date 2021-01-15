import enum
import re
from typing import Any, Dict, NamedTuple, Optional, Type, TypeVar, Union, cast

from django import forms as django_forms
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from .fields import _GT, EnumChoiceIterator, coerce_to_enum
from .widgets import Autocomplete as Autocomplete


class EnumChoiceField(django_forms.TypedChoiceField):
    def __init__(
        self, *args: Any, enum: Optional[Type[_GT]] = None, **kwargs: Any
    ) -> None:
        if enum is not None:
            self.enum = enum
            assert kwargs.get("choices", None) is None, "Pass enum or choices. Not both"
            kwargs["choices"] = EnumChoiceIterator(enum)
            kwargs["coerce"] = lambda value: coerce_to_enum(enum, value)
        else:
            self.enum = cast(EnumChoiceIterator[_GT], kwargs["choices"]).enum

        return super().__init__(*args, **kwargs)

    """
    Enum choices must be serialized to their name rather than their enum
    representation for the existing value in forms. Choices themselves are
    handled by the `choices` argument in form and model fields.
    """

    def prepare_value(self, value: Optional[enum.Enum]) -> Optional[str]:
        if isinstance(value, enum.Enum):
            return value.name
        return value


T = TypeVar("T")


class FormOrFormSetDescriptor(NamedTuple):
    prefix: Optional[str]
    field_name: str


def get_form_or_form_set_descriptor(prefixed_name: str) -> FormOrFormSetDescriptor:
    FORM_SET_REGEX = "(.*)?(-[0-9]-)(.*)"
    FORM_REGEX = "(.*)?(-)(.*)"

    form_set_match = re.match(FORM_SET_REGEX, prefixed_name)
    form_match = re.match(FORM_REGEX, prefixed_name)

    if form_set_match is not None:
        return FormOrFormSetDescriptor(
            field_name=form_set_match.groups()[2], prefix=form_set_match.groups()[0]
        )
    elif form_match is not None:
        return FormOrFormSetDescriptor(
            field_name=form_match.groups()[2], prefix=form_match.groups()[0]
        )

    return FormOrFormSetDescriptor(field_name=prefixed_name, prefix=None)


def get_form_from_form_set_or_form(
    context_data: Dict[
        str, Union[django_forms.BaseForm, django_forms.formsets.BaseFormSet, object]
    ],
    descriptor: FormOrFormSetDescriptor,
) -> Optional[django_forms.BaseForm]:

    for key, item in context_data.items():
        if isinstance(item, django_forms.BaseForm) and item.prefix == descriptor.prefix:
            return item
        elif (
            isinstance(item, django_forms.formsets.BaseFormSet)
            and item.prefix == descriptor.prefix
        ):
            return cast(django_forms.BaseForm, item.empty_form)

    return None


def autocomplete(view_func: T) -> T:
    def wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response: HttpResponse = view_func(  # type: ignore[operator]
            request, *args, **kwargs
        )
        autocomplete = request.GET.get("autocomplete", None)
        query = request.GET.get("query", "")

        if autocomplete is None or not isinstance(response, TemplateResponse):
            return response

        context_data = response.context_data or {}
        descriptor = get_form_or_form_set_descriptor(autocomplete)
        form = get_form_from_form_set_or_form(context_data, descriptor)

        if (
            form is not None
            and descriptor.field_name in form.fields
            and isinstance(
                form.fields[descriptor.field_name], django_forms.ModelChoiceField
            )
            and isinstance(form.fields[descriptor.field_name].widget, Autocomplete)
        ):
            autocomplete_field = form.fields[descriptor.field_name]
            to_field_name = autocomplete_field.to_field_name or "pk"

            results = [
                {"value": getattr(result, to_field_name), "label": str(result)}
                for result in autocomplete_field.queryset.autocomplete(query)[:50]
            ]

            return JsonResponse({"results": results})

        return response

    return cast(T, wrapped_view)
