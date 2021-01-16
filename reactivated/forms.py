import enum
import re
from typing import (
    Any,
    Callable,
    Dict,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from django import forms as django_forms
from django.forms.widgets import Widget
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from .fields import _GT, EnumChoiceIterator, coerce_to_enum
from .widgets import Autocomplete as Autocomplete


class EnumChoiceField(django_forms.TypedChoiceField):
    def __init__(
        self,
        *,
        coerce: Optional[Callable[[Any], Optional[_GT]]] = None,
        empty_value: Optional[str] = "",
        enum: Optional[Type[_GT]] = None,
        choices: Optional[EnumChoiceIterator[_GT]] = None,
        required: bool = True,
        widget: Optional[Union[Widget, Type[Widget]]] = None,
        label: Optional[str] = None,
        initial: Optional[_GT] = None,
        help_text: str = "",
        error_messages: Optional[Any] = None,
        show_hidden_initial: bool = False,
        validators: Sequence[Any] = (),
        localize: bool = False,
        disabled: bool = False,
        label_suffix: Optional[Any] = None,
    ) -> None:
        """ When instantiated by a model form, choices will be populated and
        enum will not, as Django strips all but a defined set of kwargs.

        And coerce will be populated by the model as well.

        When using this field directly in a form, enum will be populated and
        choices and coerce should be None."""

        if enum is not None and choices is None:
            self.enum = enum
            choices = EnumChoiceIterator(enum)
            coerce = lambda value: coerce_to_enum(self.enum, value)
        elif enum is None and choices is not None:
            self.enum = choices.enum
        else:
            assert False, "Pass enum or choices. Not both"

        return super().__init__(
            coerce=coerce,
            empty_value=empty_value,
            choices=choices,
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            error_messages=error_messages,
            show_hidden_initial=show_hidden_initial,
            validators=validators,
            localize=localize,
            disabled=disabled,
            label_suffix=label_suffix,
        )

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
