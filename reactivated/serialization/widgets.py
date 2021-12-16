from typing import (
    Any,
    Callable,
    List,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

from django import forms

from reactivated import stubs, widgets

from . import PROXIES, Definitions, Thing, create_schema, named_tuple_schema, serialize

JSON = Any

Override = TypeVar("Override")

TYPE_HINTS = {}


def register(path: str) -> Callable[[Override], Override]:
    def inner(override: Override) -> Override:
        TYPE_HINTS[path] = override
        return override

    return inner


class OptgroupMember(NamedTuple):
    name: str
    value: Union[str, int, bool, None]
    label: str
    selected: bool


Optgroup = Tuple[None, Tuple[OptgroupMember], int]


class BaseWidgetAttrs(NamedTuple):
    id: str
    disabled: stubs.Undefined[bool] = None
    required: stubs.Undefined[bool] = None
    placeholder: stubs.Undefined[str] = None


class BaseWidget(NamedTuple):
    template_name: str

    name: str
    is_hidden: bool
    required: bool
    value: Optional[str]
    attrs: BaseWidgetAttrs

    @staticmethod
    def coerce_value(context: Any) -> Any:
        return context["value"]

    @classmethod
    def get_json_schema(
        Proxy: Type["BaseWidget"], instance: forms.Widget, definitions: Definitions,
    ) -> "Thing":
        # Subwidgets come to us as a class already.
        widget_class = instance if isinstance(instance, type) else instance.__class__

        tag = f"{widget_class.__module__}.{widget_class.__qualname__}"  # type: ignore[attr-defined]

        if Proxy is BaseWidget:
            assert False, f"Unsupported widget {tag}"

        # TODO: this should really be done automatically for the instance we're wrapping.
        definition_name = f"{Proxy.__module__}.{Proxy.__qualname__}"

        if definition_name in definitions:
            return Thing(
                schema={"$ref": f"#/definitions/{definition_name}"},
                definitions=definitions,
            )

        base = named_tuple_schema(Proxy, definitions, exclude=["subwidgets"])

        if subwidgets := get_type_hints(Proxy).get("subwidgets", None):
            if hasattr(subwidgets, "__annotations__"):
                subwidgets_tuple = Tuple[Any]
                subwidgets_tuple.__args__ = list(subwidgets.__annotations__.values())  # type: ignore[attr-defined]
                subwidget_keys = subwidgets.__annotations__.keys()
            else:
                subwidgets_tuple = subwidgets  # type: ignore[misc]
                subwidget_keys = [
                    str(index) for index in range(len(subwidgets.__args__))
                ]

            subwidgets_schema, definitions = create_schema(
                subwidgets_tuple, base.definitions
            )

            values_schema = {
                "type": "object",
                "required": [],
                "properties": {},
                "additionalProperties": False,
            }

            for subwidget_key, subwidget in zip(
                subwidget_keys, subwidgets_tuple.__args__  # type: ignore[attr-defined]
            ):
                value_schema = create_schema(subwidget, base.definitions).dereference()[
                    "properties"
                ]["value"]
                values_schema["properties"][subwidget_key] = value_schema  # type: ignore[index]
                values_schema["required"].append(subwidget_key)  # type: ignore[attr-defined]

            base = base._replace(definitions=definitions)
            base = base.add_property(
                "_reactivated_value_do_not_use", values_schema, optional=True
            )
            base = base.add_property("subwidgets", subwidgets_schema)

        base = base.add_property(
            "tag", create_schema(Literal[tag], base.definitions).schema
        )

        return base

    @classmethod
    def get_serialized_value(
        Proxy: Type["BaseWidget"], value: Any, schema: "Thing"
    ) -> JSON:
        widget_class = value.__class__
        context = value if isinstance(value, dict) else value._reactivated_get_context()

        # TODO: exclude value, and do it manually by calling get_value()
        # So call named_tuple serialized directly instead of serialize()
        serialized = serialize(context, schema, suppress_custom_serializer=True)
        serialized["tag"] = f"{widget_class.__module__}.{widget_class.__qualname__}"
        serialized["value"] = Proxy.coerce_value(context)

        if (subwidgets := get_type_hints(Proxy).get("subwidgets", None)) :
            subwidgets_to_enumerate = (
                subwidgets.__annotations__.values()
                if hasattr(subwidgets, "__annotations__")
                else subwidgets.__args__
            )

            for index, subwidget_class in enumerate(subwidgets_to_enumerate):
                serialized["subwidgets"][index][
                    "tag"
                ] = f"{subwidget_class.__module__}.{subwidget_class.__qualname__}"

        return serialized


PROXIES[forms.Widget] = BaseWidget


class MaxLengthAttrs(BaseWidgetAttrs):
    maxlength: stubs.Undefined[str]


@register("django.forms.widgets.HiddenInput")
class HiddenInput(BaseWidget):
    type: Literal["hidden"]


PROXIES[forms.HiddenInput] = HiddenInput


@register("django.forms.widgets.TextInput")
class TextInput(BaseWidget):
    type: Literal["text"]
    attrs: MaxLengthAttrs


PROXIES[forms.TextInput] = TextInput


@register("django.forms.widgets.URLInput")
class URLInput(BaseWidget):
    type: Literal["url"]
    attrs: MaxLengthAttrs


PROXIES[forms.URLInput] = URLInput


class StepAttrs(BaseWidgetAttrs):
    step: Optional[str]


@register("django.forms.widgets.NumberInput")
class NumberInput(BaseWidget):
    type: Literal["number"]
    attrs: StepAttrs


PROXIES[forms.NumberInput] = NumberInput


class TimeAttrs(BaseWidgetAttrs):
    format: Optional[str]


@register("django.forms.widgets.TimeInput")
class TimeInput(BaseWidget):
    type: Literal["text"]
    attrs: TimeAttrs


PROXIES[forms.TimeInput] = TimeInput


class DateAttrs(BaseWidgetAttrs):
    format: Optional[str]


@register("django.forms.widgets.DateInput")
class DateInput(BaseWidget):
    type: Literal["text"]
    attrs: DateAttrs


PROXIES[forms.DateInput] = DateInput


class DateTimeAttrs(BaseWidgetAttrs):
    format: str


@register("django.forms.widgets.DateTimeInput")
class DateTimeInput(BaseWidget):
    type: Literal["text"]
    attrs: DateTimeAttrs


class CheckAttrs(BaseWidgetAttrs):
    checked: stubs.Undefined[bool]


@register("django.forms.widgets.CheckboxInput")
class CheckboxInput(BaseWidget):
    type: Literal["checkbox"]
    attrs: CheckAttrs
    value: bool  # type: ignore[assignment]

    @staticmethod
    def coerce_value(context: Any) -> bool:
        return context["attrs"].get("checked", False) is True


PROXIES[forms.CheckboxInput] = CheckboxInput


@register("django.forms.widgets.PasswordInput")
class PasswordInput(BaseWidget):
    type: Literal["password"]


PROXIES[forms.PasswordInput] = PasswordInput


@register("django.forms.widgets.EmailInput")
class EmailInput(BaseWidget):
    type: Literal["email"]


PROXIES[forms.EmailInput] = EmailInput


class TextareaAttrs(BaseWidgetAttrs):
    cols: str
    rows: str


@register("django.forms.widgets.Textarea")
class Textarea(BaseWidget):
    attrs: TextareaAttrs


PROXIES[forms.Textarea] = Textarea


@register("django.forms.widgets.Select")
class Select(BaseWidget):
    optgroups: List[Optgroup]
    value: List[str]  # type: ignore[assignment]


PROXIES[forms.Select] = Select


class SelectMultipleAttrs(BaseWidgetAttrs):
    multiple: bool


@register("django.forms.widgets.SelectMultiple")
class SelectMultiple(BaseWidget):
    attrs: SelectMultipleAttrs
    optgroups: List[Optgroup]
    value: List[str]  # type: ignore[assignment]


PROXIES[forms.SelectMultiple] = SelectMultiple


@register("taggit.forms.TagWidget")
class TagWidget(TextInput):
    pass


@register("django.forms.widgets.ClearableFileInput")
class ClearableFileInput(BaseWidget):
    type: Literal["file"]
    checkbox_name: str
    checkbox_id: str
    is_initial: bool
    input_text: str
    initial_text: str
    clear_checkbox_label: str


PROXIES[forms.ClearableFileInput] = ClearableFileInput


class SelectDateWidgetValue(NamedTuple):
    year: Optional[Union[str, int]]
    month: Optional[Union[str, int]]
    day: Optional[Union[str, int]]


class SelectDateWidgetSubwidgets(NamedTuple):
    year: forms.Select
    month: forms.Select
    day: forms.Select


@register("django.forms.widgets.SelectDateWidget")
class SelectDateWidget(BaseWidget):
    subwidgets: SelectDateWidgetSubwidgets
    value: Any


PROXIES[forms.SelectDateWidget] = SelectDateWidget


@register("django.forms.widgets.SplitDateTimeWidget")
class SplitDateTimeWidget(BaseWidget):
    subwidgets: Tuple[forms.DateInput, forms.TimeInput]
    value: Any


PROXIES[forms.SplitDateTimeWidget] = SplitDateTimeWidget


class AutocompleteSelected(NamedTuple):
    value: Union[str, int]
    label: str


class Autocomplete(BaseWidget):
    value: List[str]  # type: ignore[assignment]
    selected: Optional[AutocompleteSelected]


PROXIES[widgets.Autocomplete] = Autocomplete
