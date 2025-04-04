import enum
import re
from collections.abc import Callable, Sequence
from enum import unique
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NamedTuple,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from django import forms as django_forms
from django.forms.widgets import Widget
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from . import registry, serialization, stubs
from .fields import _GT, EnumChoiceIterator, coerce_to_enum
from .widgets import Autocomplete as Autocomplete

if TYPE_CHECKING:
    from django.forms.formsets import _F
    from django.forms.models import _M, _ModelFormT

    class FormSetFactory(django_forms.BaseFormSet[_F]):
        pass

    class ModelFormSetFactory(django_forms.BaseModelFormSet[_M, _ModelFormT]):
        pass

else:

    class FormSetFactory:
        def __class_getitem__(cls: Any, item: Any) -> Any:
            return django_forms.formset_factory(form=item)

    class ModelFormSetFactory:
        def __class_getitem__(cls: Any, item: Any) -> Any:
            model, form = item
            return django_forms.modelformset_factory(model=model, form=form)


class EnumChoiceField(django_forms.TypedChoiceField):
    def __init__(
        self,
        *,
        coerce: Callable[[Any], _GT | None] | None = None,
        empty_value: str | None = "",
        enum: type[_GT] | None = None,
        choices: EnumChoiceIterator[_GT] | None = None,
        required: bool = True,
        widget: Widget | type[Widget] | None = None,
        label: str | None = None,
        initial: _GT | None = None,
        help_text: str = "",
        error_messages: Any | None = None,
        show_hidden_initial: bool = False,
        validators: Sequence[Any] = (),
        localize: bool = False,
        disabled: bool = False,
        label_suffix: Any | None = None,
    ) -> None:
        """When instantiated by a model form, choices will be populated and
        enum will not, as Django strips all but a defined set of kwargs.

        And coerce will be populated by the model as well.

        When using this field directly in a form, enum will be populated and
        choices and coerce should be None."""

        if enum is not None and choices is None:
            self.enum = enum
            choices = EnumChoiceIterator(enum=enum, include_blank=required)
            coerce = lambda value: coerce_to_enum(self.enum, value)
        elif enum is None and choices is not None:
            self.enum = choices.enum
        else:
            assert False, "Pass enum or choices. Not both"

        unique(self.enum)

        return super().__init__(
            coerce=coerce,  # type: ignore[arg-type]
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

    def prepare_value(self, value: enum.Enum | None) -> str | None:
        if isinstance(value, enum.Enum):
            return value.name
        return value


T = TypeVar("T")


class FormOrFormSetDescriptor(NamedTuple):
    prefix: str | None
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
    context_data: dict[
        str,
        django_forms.BaseForm | django_forms.formsets.BaseFormSet[Any] | object,
    ],
    descriptor: FormOrFormSetDescriptor,
) -> django_forms.BaseForm | None:
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
            to_field_name = autocomplete_field.to_field_name or "pk"  # type: ignore[attr-defined]

            results = [
                {"value": getattr(result, to_field_name), "label": str(result)}
                for result in autocomplete_field.queryset.autocomplete(query)[:50]  # type: ignore[attr-defined]
            ]

            return JsonResponse({"results": results})

        return response

    return cast(T, wrapped_view)


class FormGroup:
    tag: Literal["FormGroup"] = "FormGroup"

    def __init__(self, data: Any = None) -> None:
        hints = get_type_hints(type(self))

        without_none = {}

        for hint_name, hint in hints.items():
            if hint_name == "tag":
                continue

            if isinstance(hint, stubs._GenericAlias) and issubclass(
                hint.__args__[1], type(None)
            ):
                without_none[hint_name] = hint.__args__[0]
            else:
                without_none[hint_name] = hint

        for arg_name, arg_type in without_none.items():
            setattr(self, arg_name, arg_type(data, prefix=arg_name))

    @property
    def errors(self) -> Any:
        collected = {}

        for arg_name in get_type_hints(self).keys():
            collected[arg_name] = getattr(self, arg_name).errors

        return collected

    def is_valid(self) -> bool:
        return all(
            [
                getattr(self, arg_name).is_valid()
                for arg_name in get_type_hints(self).keys()
            ]
        )

    @classmethod
    def get_json_schema(_Type, definitions: registry.Definitions) -> registry.Thing:
        return serialization.named_tuple_schema(_Type, definitions, exclude=["errors"])

    @classmethod
    def get_serialized_value(
        _Type: type["FormGroup"],
        class_or_instance: Union[type["FormGroup"], "FormGroup"],
        schema: registry.Thing,
    ) -> registry.JSON:
        # if isinstance(class_or_instance, FormGroup):
        #     assert False, "Not yet supported"

        if isinstance(class_or_instance, FormGroup):
            return {
                **serialization.serialize(
                    class_or_instance,
                    schema,
                    suppress_custom_serializer=True,
                ),
                "tag": "FormGroup",
            }

        hints = (
            get_type_hints(type(class_or_instance))
            if isinstance(class_or_instance, FormGroup)
            else get_type_hints(class_or_instance)
        )

        without_none = {}

        for hint_name, hint in hints.items():
            if hint_name == "tag":
                continue

            if isinstance(hint, stubs._GenericAlias) and issubclass(
                hint.__args__[1], type(None)
            ):
                without_none[hint_name] = hint.__args__[0]
            else:
                without_none[hint_name] = hint

        return {
            **serialization.serialize(
                without_none,
                schema,
                suppress_custom_serializer=True,
            ),
            "tag": "FormGroup",
        }
