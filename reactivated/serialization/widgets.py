from typing import (
    Any,
    Dict,
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

from reactivated import stubs

from .registry import (
    JSON,
    DefaultWidgetType,
    Definitions,
    Thing,
    global_types,
    register,
)

Override = TypeVar("Override")


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


@register(forms.Widget)
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
        Proxy: Type["BaseWidget"],
        instance: forms.Widget,
        definitions: Definitions,
    ) -> "Thing":
        from . import create_schema, named_tuple_schema

        # Subwidgets come to us as a class already.
        widget_class: Type[forms.Widget] = instance if isinstance(instance, type) else instance.__class__  # type: ignore[assignment]
        tag = f"{widget_class.__module__}.{widget_class.__qualname__}"

        if Proxy is BaseWidget:
            assert False, f"Unsupported widget {tag}"

        # TODO: this should really be done automatically for the instance we're wrapping.
        definition_name = tag  # f"{Proxy.__module__}.{Proxy.__qualname__}"

        if definition_name in definitions:
            return Thing(
                schema={"$ref": f"#/definitions/{definition_name}"},
                definitions=definitions,
            )

        base = named_tuple_schema(
            Proxy, definitions, definition_name=definition_name, exclude=["subwidgets"]
        )
        base = base.add_property("template_name", create_schema(Literal[widget_class.template_name], {}).schema)  # type: ignore[attr-defined]

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
        GlobalWidget: Dict[str, Any] = (
            global_types["Widget"]
            if global_types["Widget"] is not DefaultWidgetType
            else {
                "anyOf": [],
            }
        )

        GlobalWidget = {
            **GlobalWidget,
            "anyOf": [
                *GlobalWidget["anyOf"],
                base.schema,
            ],
        }
        global_types["Widget"] = GlobalWidget

        return base

    @classmethod
    def get_serialized_value(
        Proxy: Type["BaseWidget"], value: Any, schema: "Thing"
    ) -> JSON:
        from . import serialize

        widget_class = value.__class__
        context = value if isinstance(value, dict) else value._reactivated_get_context()

        # TODO: exclude value, and do it manually by calling get_value()
        # So call named_tuple serialized directly instead of serialize()
        serialized = serialize(context, schema, suppress_custom_serializer=True)
        serialized["tag"] = f"{widget_class.__module__}.{widget_class.__qualname__}"
        serialized["value"] = Proxy.coerce_value(context)

        if subwidgets := get_type_hints(Proxy).get("subwidgets", None):
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


class MaxLengthAttrs(BaseWidgetAttrs):
    maxlength: stubs.Undefined[str]


@register(forms.HiddenInput)
class HiddenInput(BaseWidget):
    template_name: Literal["django/forms/widgets/hidden.html"]
    type: Literal["hidden"]


@register(forms.TextInput)
class TextInput(BaseWidget):
    template_name: Literal["django/forms/widgets/text.html"]
    type: Literal["text"]
    attrs: MaxLengthAttrs


@register(forms.URLInput)
class URLInput(BaseWidget):
    template_name: Literal["django/forms/widgets/url.html"]
    type: Literal["url"]
    attrs: MaxLengthAttrs


class StepAttrs(BaseWidgetAttrs):
    step: stubs.Undefined[str]


@register(forms.NumberInput)
class NumberInput(BaseWidget):
    template_name: Literal["django/forms/widgets/number.html"]
    type: Literal["number"]
    attrs: StepAttrs


class TimeAttrs(BaseWidgetAttrs):
    format: stubs.Undefined[str]


@register(forms.TimeInput)
class TimeInput(BaseWidget):
    template_name: Literal["django/forms/widgets/time.html"]
    type: Literal["text"]
    attrs: TimeAttrs


class DateAttrs(BaseWidgetAttrs):
    format: stubs.Undefined[str]


@register(forms.DateInput)
class DateInput(BaseWidget):
    template_name: Literal["django/forms/widgets/date.html"]
    type: Literal["text"]
    attrs: DateAttrs


class DateTimeAttrs(BaseWidgetAttrs):
    format: str


@register(forms.DateTimeInput)
class DateTimeInput(BaseWidget):
    template_name: Literal["django/forms/widgets/datetime.html"]
    type: Literal["text"]
    attrs: DateTimeAttrs


class CheckAttrs(BaseWidgetAttrs):
    checked: stubs.Undefined[bool]


@register(forms.CheckboxInput)
class CheckboxInput(BaseWidget):
    template_name: Literal["django/forms/widgets/checkbox.html"]
    type: Literal["checkbox"]
    attrs: CheckAttrs
    value: bool  # type: ignore[assignment]

    @staticmethod
    def coerce_value(context: Any) -> bool:
        return context["attrs"].get("checked", False) is True


@register(forms.PasswordInput)
class PasswordInput(BaseWidget):
    template_name: Literal["django/forms/widgets/password.html"]
    type: Literal["password"]


@register(forms.EmailInput)
class EmailInput(BaseWidget):
    template_name: Literal["django/forms/widgets/email.html"]
    type: Literal["email"]


class TextareaAttrs(BaseWidgetAttrs):
    cols: str
    rows: str


@register(forms.Textarea)
class Textarea(BaseWidget):
    template_name: Literal["django/forms/widgets/textarea.html"]
    attrs: TextareaAttrs


@register(forms.Select)
class Select(BaseWidget):
    template_name: Literal["django/forms/widgets/select.html"]
    optgroups: List[Optgroup]

    @staticmethod
    def coerce_value(context: Any) -> Any:
        return context["value"][0]


class SelectMultipleAttrs(BaseWidgetAttrs):
    multiple: bool


@register(forms.SelectMultiple)
class SelectMultiple(BaseWidget):
    attrs: SelectMultipleAttrs
    optgroups: List[Optgroup]
    value: List[str]  # type: ignore[assignment]


@register(forms.ClearableFileInput)
class ClearableFileInput(BaseWidget):
    template_name: Literal["django/forms/widgets/clearable_file_input.html"]
    type: Literal["file"]
    checkbox_name: str
    checkbox_id: str
    is_initial: bool
    input_text: str
    initial_text: str
    clear_checkbox_label: str


class SelectDateWidgetValue(NamedTuple):
    year: Optional[Union[str, int]]
    month: Optional[Union[str, int]]
    day: Optional[Union[str, int]]


class SelectDateWidgetSubwidgets(NamedTuple):
    year: forms.Select
    month: forms.Select
    day: forms.Select


@register(forms.SelectDateWidget)
class SelectDateWidget(BaseWidget):
    template_name: Literal["django/forms/widgets/select_date.html"]
    subwidgets: SelectDateWidgetSubwidgets
    value: Any


@register(forms.SplitDateTimeWidget)
class SplitDateTimeWidget(BaseWidget):
    template_name: Literal["django/forms/widgets/splitdatetime.html"]
    subwidgets: Tuple[forms.DateInput, forms.TimeInput]
    value: Any
