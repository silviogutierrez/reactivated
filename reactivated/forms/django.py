import enum
from collections.abc import Callable, Sequence
from enum import unique
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeVar,
)

from django import forms as django_forms
from django.forms.widgets import Widget

from ..fields import _GT, EnumChoiceIterator, coerce_to_enum
from ..registry import definitions_registry
from ..rpc.core import Pick
from ..utils import ClassLookupDict
from .schema import create_schema as reactivated_create_schema

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


# --- Django forms -> pydantic bridge (DjangoForm / DjangoFormSet) ---------

from typing import Annotated, Generic, get_args  # noqa: E402

from django import forms  # noqa: E402
from pydantic import (  # noqa: E402
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    TypeAdapter,
)
from pydantic.json_schema import JsonSchemaValue  # noqa: E402
from pydantic_core import core_schema  # noqa: E402


class _UndefinedMarker(Generic[T]):
    """
    Marker for Pydantic to generate optional TypeScript fields.

    Usage:
        class MyAttrs(Pick):
            id: str
            disabled: Undefined[bool] = None  # generates: disabled?: boolean

    This differs from `bool | None` which generates `disabled: boolean | null`.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Extract the inner type T from Undefined[T]
        args = get_args(source_type)
        inner_type = args[0] if args else Any

        # Allow None at runtime but don't include in schema type
        inner_schema = handler(inner_type)

        return core_schema.nullable_schema(inner_schema)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Get the inner type's schema (without null)
        inner_schema = cs.get("schema", {})
        if inner_schema:
            return handler(inner_schema)
        return {}


# Type alias: Undefined[T] means "optional T" in TypeScript (field?: T)
Undefined = Annotated[T | None, _UndefinedMarker[T]]


_widget_registry: ClassLookupDict = ClassLookupDict({})

TWidget = TypeVar("TWidget", bound=forms.Widget)
TSchema = TypeVar("TSchema", bound=type[Pick])


def register_widget(
    widget_class: type[TWidget],
) -> Callable[[TSchema], TSchema]:
    def decorator(schema_class: TSchema) -> TSchema:
        _widget_registry[widget_class] = schema_class
        return schema_class

    return decorator


def get_widget_schema_class(widget: forms.Widget) -> type[Pick] | None:
    try:
        return _widget_registry[widget.__class__]  # type: ignore[no-any-return]
    except KeyError:
        return None


class OptgroupMember(Pick):
    name: str
    value: str | int | bool | None
    label: str
    selected: bool


Optgroup = tuple[None, tuple[OptgroupMember, ...], int]


class BaseWidgetAttrs(Pick):
    id: str
    disabled: Undefined[bool] = None
    required: Undefined[bool] = None
    placeholder: Undefined[str] = None


class MaxLengthAttrs(BaseWidgetAttrs):
    maxlength: Undefined[str] = None


class StepAttrs(BaseWidgetAttrs):
    step: Undefined[str] = None


class CheckAttrs(BaseWidgetAttrs):
    checked: Undefined[bool] = None


class TextareaAttrs(BaseWidgetAttrs):
    cols: Undefined[str] = None
    rows: Undefined[str] = None


class SelectMultipleAttrs(BaseWidgetAttrs):
    multiple: bool = True


class BaseWidgetSchema(Pick):
    template_name: str
    name: str
    is_hidden: bool
    required: bool
    value: Any
    attrs: dict[str, Any]
    tag: str


@register_widget(forms.HiddenInput)
class HiddenInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/hidden.html"]
    type: Literal["hidden"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]


@register_widget(forms.TextInput)
class TextInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/text.html"]
    type: Literal["text"]
    value: str | None
    attrs: MaxLengthAttrs  # type: ignore[assignment]


@register_widget(forms.URLInput)
class URLInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/url.html"]
    type: Literal["url"]
    value: str | None
    attrs: MaxLengthAttrs  # type: ignore[assignment]


@register_widget(forms.NumberInput)
class NumberInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/number.html"]
    type: Literal["number"]
    value: str | None
    attrs: StepAttrs  # type: ignore[assignment]


@register_widget(forms.TimeInput)
class TimeInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/time.html"]
    type: Literal["text"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]


@register_widget(forms.DateInput)
class DateInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/date.html"]
    type: Literal["text"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]


@register_widget(forms.DateTimeInput)
class DateTimeInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/datetime.html"]
    type: Literal["text"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]


@register_widget(forms.CheckboxInput)
class CheckboxInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/checkbox.html"]
    type: Literal["checkbox"]
    value: bool
    attrs: CheckAttrs  # type: ignore[assignment]


@register_widget(forms.PasswordInput)
class PasswordInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/password.html"]
    type: Literal["password"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]


@register_widget(forms.EmailInput)
class EmailInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/email.html"]
    type: Literal["email"]
    value: str | None
    attrs: MaxLengthAttrs  # type: ignore[assignment]


@register_widget(forms.Textarea)
class TextareaSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/textarea.html"]
    value: str | None
    attrs: TextareaAttrs  # type: ignore[assignment]


@register_widget(forms.Select)
class SelectSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/select.html"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]
    optgroups: list[Optgroup]


@register_widget(forms.SelectMultiple)
class SelectMultipleSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/select.html"]
    value: list[str]
    attrs: SelectMultipleAttrs  # type: ignore[assignment]
    optgroups: list[Optgroup]


@register_widget(forms.SelectDateWidget)
class SelectDateWidgetSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/select_date.html"]
    value: Any
    attrs: BaseWidgetAttrs  # type: ignore[assignment]


@register_widget(forms.ClearableFileInput)
class ClearableFileInputSchema(BaseWidgetSchema):
    template_name: Literal["django/forms/widgets/clearable_file_input.html"]
    type: Literal["file"]
    value: str | None
    attrs: BaseWidgetAttrs  # type: ignore[assignment]
    checkbox_name: str
    checkbox_id: str
    is_initial: bool
    input_text: str
    initial_text: str
    clear_checkbox_label: str


class FieldSchema(Pick):
    name: str
    label: str
    help_text: str | None
    widget: BaseWidgetSchema


def _process_optgroups(context: dict[str, Any]) -> None:
    optgroups = context.get("optgroups")
    if optgroups is not None:
        context["optgroups"] = [
            (
                group_name,
                tuple(
                    {
                        "name": opt["name"],
                        "value": (
                            str(opt["value"]) if opt["value"] is not None else None
                        ),
                        "label": str(opt["label"]),
                        "selected": opt["selected"],
                    }
                    for opt in options
                ),
                index,
            )
            for group_name, options, index in optgroups
        ]


def extract_widget_context(bound_field: forms.BoundField) -> dict[str, Any]:
    original_render = bound_field.field.widget._render
    bound_field.field.widget._render = lambda template_name, context, renderer: context
    widget_context: Any = bound_field.as_widget()
    context: dict[str, Any] = widget_context["widget"]

    context["template_name"] = getattr(
        bound_field.field.widget, "reactivated_widget", context["template_name"]
    )

    for subwidget_context in context.get("subwidgets", []):
        _process_optgroups(subwidget_context)

    _process_optgroups(context)

    bound_field.field.widget._render = original_render
    return context


def coerce_widget_value(widget: forms.Widget, context: dict[str, Any]) -> Any:
    if isinstance(widget, forms.CheckboxInput):
        return context["attrs"].get("checked", False) is True
    elif isinstance(widget, forms.Select) and not isinstance(
        widget, forms.SelectMultiple
    ):
        value = context.get("value")
        return value[0] if value else None
    return context.get("value")


def get_widget_json_schema(
    widget: forms.Widget, handler: GetJsonSchemaHandler
) -> dict[str, Any]:
    widget_class = widget.__class__
    widget_tag = f"{widget_class.__module__}.{widget_class.__qualname__}"

    # Register in reactivated's global Widget union for backward compatibility.
    if widget_tag not in definitions_registry:
        try:
            result = reactivated_create_schema(widget, definitions_registry)
            definitions_registry.update(result.definitions)
        except (KeyError, AssertionError):
            pass

    # Handle SelectDateWidget specially - it needs subwidgets in the schema
    if isinstance(widget, forms.SelectDateWidget):
        attrs_adapter = TypeAdapter(BaseWidgetAttrs)
        attrs_schema = handler(attrs_adapter.core_schema)
        select_schema = get_widget_json_schema(forms.Select(), handler)
        return {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "const": "django/forms/widgets/select_date.html",
                },
                "name": {"type": "string"},
                "is_hidden": {"type": "boolean"},
                "required": {"type": "boolean"},
                "value": {},
                "attrs": attrs_schema,
                "tag": {"type": "string", "const": widget_tag},
                "subwidgets": {
                    "type": "array",
                    "items": [select_schema, select_schema, select_schema],
                    "maxItems": 3,
                    "minItems": 3,
                },
            },
            "required": [
                "template_name",
                "name",
                "is_hidden",
                "required",
                "value",
                "attrs",
                "tag",
                "subwidgets",
            ],
        }

    # Check registry for typed schema
    schema_class = get_widget_schema_class(widget)

    if schema_class is not None:
        # Use the shared handler to generate schema - this adds any nested
        # types (like MaxLengthAttrs) to the parent schema's $defs registry
        adapter = TypeAdapter(schema_class)
        widget_schema = handler(adapter.core_schema)

        # Override tag to be the actual widget class (not the schema class)
        if "properties" in widget_schema and "tag" in widget_schema["properties"]:
            widget_schema["properties"]["tag"] = {"type": "string", "const": widget_tag}

        return widget_schema

    # Fallback: generate generic schema
    fallback_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "template_name": {"type": "string"},
            "name": {"type": "string"},
            "is_hidden": {"type": "boolean"},
            "required": {"type": "boolean"},
            "value": {},
            "attrs": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
            "tag": {"type": "string", "const": widget_tag},
        },
        "required": [
            "template_name",
            "name",
            "is_hidden",
            "required",
            "value",
            "attrs",
            "tag",
        ],
    }

    # Add widget-specific properties
    if isinstance(widget, (forms.Select, forms.SelectMultiple)):
        fallback_schema["properties"]["optgroups"] = {"type": "array"}
    if isinstance(widget, forms.CheckboxInput):
        fallback_schema["properties"]["value"] = {"type": "boolean"}
    elif isinstance(widget, forms.SelectMultiple):
        fallback_schema["properties"]["value"] = {
            "type": "array",
            "items": {"type": "string"},
        }
    else:
        fallback_schema["properties"]["value"] = {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        }

    return fallback_schema


TForm = TypeVar("TForm", bound=forms.BaseForm)


class DjangoForm:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # source_type is the form class from Annotated[FormClass, DjangoForm]
        form_class = source_type

        def validate(value: Any) -> forms.BaseForm:
            if isinstance(value, forms.BaseForm):
                return value
            raise ValueError(f"Expected a Django form, got {type(value)}")

        def serialize(
            value: forms.BaseForm, info: core_schema.SerializationInfo
        ) -> dict[str, Any]:
            if info.mode != "json":
                return value  # type: ignore[return-value]

            form = value
            context = form.get_context()
            hidden_fields = {f.name: f for f in context["hidden_fields"]}
            visible_fields = {f.name: f for f, _ in context["fields"]}
            all_fields = {**hidden_fields, **visible_fields}

            fields = {}
            for field_name, bound_field in all_fields.items():
                widget_context = extract_widget_context(bound_field)
                widget_class = bound_field.field.widget.__class__

                fields[field_name] = {
                    "name": field_name,
                    "label": (
                        str(bound_field.label)
                        if bound_field.label is not None
                        else field_name
                    ),
                    "help_text": (
                        str(bound_field.help_text) if bound_field.help_text else None
                    ),
                    "widget": {
                        "template_name": widget_context["template_name"],
                        "name": widget_context["name"],
                        "is_hidden": bound_field.is_hidden,
                        "required": bound_field.field.required,
                        "value": coerce_widget_value(
                            bound_field.field.widget, widget_context
                        ),
                        "attrs": {
                            "id": bound_field.id_for_label or bound_field.html_name,
                            **widget_context.get("attrs", {}),
                        },
                        "tag": f"{widget_class.__module__}.{widget_class.__qualname__}",
                        **(
                            {"optgroups": widget_context["optgroups"]}
                            if "optgroups" in widget_context
                            else {}
                        ),
                        **(
                            {"type": widget_context["type"]}
                            if "type" in widget_context
                            else {}
                        ),
                    },
                }

                # Handle subwidgets for multi-widgets (e.g., SelectDateWidget)
                subwidgets_context = widget_context.get("subwidgets")
                if subwidgets_context is not None:
                    serialized_subwidgets = []
                    for sw_context in subwidgets_context:
                        sw_value = sw_context.get("value")
                        if isinstance(sw_value, list):
                            sw_value = sw_value[0] if sw_value else None
                        serialized_subwidgets.append(
                            {
                                "template_name": sw_context["template_name"],
                                "name": sw_context["name"],
                                "is_hidden": False,
                                "required": bound_field.field.required,
                                "value": sw_value,
                                "attrs": sw_context.get("attrs", {}),
                                "tag": f"{forms.Select.__module__}.{forms.Select.__qualname__}",
                                **(
                                    {"optgroups": sw_context["optgroups"]}
                                    if "optgroups" in sw_context
                                    else {}
                                ),
                            }
                        )
                    fields[field_name]["widget"]["subwidgets"] = serialized_subwidgets

                from reactivated.forms import EnumChoiceField

                if isinstance(bound_field.field, EnumChoiceField):
                    current_value = bound_field.value()
                    fields[field_name]["enum"] = (
                        current_value if current_value else None
                    )

            errors = None
            if form.errors:
                errors = {k: list(v) for k, v in form.errors.items()}

            return {
                "name": f"{form.__class__.__module__}.{form.__class__.__qualname__}",
                "errors": errors,
                "fields": fields,
                "iterator": list(hidden_fields.keys()) + list(visible_fields.keys()),
                "hidden_fields": list(hidden_fields.keys()),
                "prefix": form.prefix or "",
            }

        schema = core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, info_arg=True
            ),
            metadata={"form_class": form_class},
        )
        return schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Extract form class stored in metadata during core schema building
        metadata = cs.get("metadata", {})
        form_class = metadata.get("form_class", forms.Form) if metadata else forms.Form
        form_name = f"{form_class.__module__}.{form_class.__qualname__}"

        field_properties = {}
        field_required: list[str] = []
        error_properties: dict[str, Any] = {}

        for field_name, field in form_class.base_fields.items():
            field_required.append(field_name)

            # Get widget schema (uses registry if available)
            # Pass handler so $defs are added to the shared registry
            widget_schema = get_widget_json_schema(field.widget, handler)

            # Build field schema
            field_schema: dict[str, Any] = {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "const": field_name},
                    "label": {"type": "string"},
                    "help_text": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "widget": widget_schema,
                },
                "required": ["name", "label", "help_text", "widget"],
            }

            # Handle EnumChoiceField - add enum property
            from reactivated.forms import EnumChoiceField

            if isinstance(field, EnumChoiceField):
                enum_values = list(field.enum.__members__.keys())
                field_schema["properties"]["enum"] = {
                    "anyOf": [
                        {"type": "string", "enum": enum_values},
                        {"type": "null"},
                    ]
                }
                field_schema["required"].append("enum")

            # Handle UUIDField
            if isinstance(field, forms.UUIDField):
                field_schema["properties"]["enum"] = {"tsType": "UUID | null"}
                field_schema["required"].append("enum")

            field_properties[field_name] = field_schema
            error_properties[field_name] = {
                "type": "array",
                "items": {"type": "string"},
            }

        iterator_schema = (
            {"type": "array", "items": {"type": "string", "enum": field_required}}
            if field_required
            else {"type": "array", "items": []}
        )

        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "const": form_name},
                "errors": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": error_properties,
                            "additionalProperties": False,
                            "required": [],
                        },
                        {"type": "null"},
                    ]
                },
                "fields": {
                    "type": "object",
                    "properties": field_properties,
                    "required": field_required,
                    "additionalProperties": False,
                },
                "iterator": iterator_schema,
                "hidden_fields": iterator_schema,
                "prefix": {"type": "string"},
            },
            "required": [
                "name",
                "errors",
                "fields",
                "iterator",
                "hidden_fields",
                "prefix",
            ],
            "additionalProperties": False,
        }


TFormSet = TypeVar("TFormSet", bound=forms.BaseFormSet[Any])


class DjangoFormSet:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # source_type is the formset class from Annotated[FormSetClass, DjangoFormSet]
        formset_class = source_type

        def validate(value: Any) -> forms.BaseFormSet[Any]:
            if isinstance(value, forms.BaseFormSet):
                return value
            raise ValueError(f"Expected a Django formset, got {type(value)}")

        def serialize(
            value: forms.BaseFormSet[Any], info: core_schema.SerializationInfo
        ) -> dict[str, Any]:
            if info.mode != "json":
                return value  # type: ignore[return-value]

            formset = value
            form_class = formset.form

            form_schema = DjangoForm.__get_pydantic_core_schema__(form_class, handler)
            form_serialize = form_schema["serialization"]["function"]

            serialized_forms = [form_serialize(form, info) for form in formset.forms]
            empty_form_serialized = form_serialize(formset.empty_form, info)
            management_form_serialized = form_serialize(formset.management_form, info)

            return {
                "initial_form_count": formset.initial_form_count(),
                "total_form_count": formset.total_form_count(),
                "max_num": formset.max_num,
                "min_num": formset.min_num,
                "can_delete": formset.can_delete,
                "can_order": formset.can_order,
                "non_form_errors": list(formset.non_form_errors()),
                "forms": serialized_forms,
                "empty_form": empty_form_serialized,
                "management_form": management_form_serialized,
                "prefix": formset.prefix or "",
            }

        schema = core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, info_arg=True
            ),
            metadata={"formset_class": formset_class},
        )
        return schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Extract formset class stored in metadata during core schema building
        metadata = cs.get("metadata", {})
        formset_class: type[forms.BaseFormSet[Any]] = (
            metadata.get("formset_class", forms.BaseFormSet)
            if metadata
            else forms.BaseFormSet
        )
        form_class: type[forms.BaseForm] = formset_class.form

        # Build core schema with form_class in metadata for JSON schema generation
        form_cs: dict[str, Any] = {"metadata": {"form_class": form_class}}
        form_schema = DjangoForm.__get_pydantic_json_schema__(form_cs, handler)

        management_cs: dict[str, Any] = {
            "metadata": {"form_class": forms.formsets.ManagementForm}
        }
        management_form_schema = DjangoForm.__get_pydantic_json_schema__(
            management_cs, handler
        )

        return {
            "type": "object",
            "properties": {
                "initial_form_count": {"type": "integer"},
                "total_form_count": {"type": "integer"},
                "max_num": {"type": "integer"},
                "min_num": {"type": "integer"},
                "can_delete": {"type": "boolean"},
                "can_order": {"type": "boolean"},
                "non_form_errors": {"type": "array", "items": {"type": "string"}},
                "forms": {"type": "array", "items": form_schema},
                "empty_form": form_schema,
                "management_form": management_form_schema,
                "prefix": {"type": "string"},
            },
            "required": [
                "initial_form_count",
                "total_form_count",
                "max_num",
                "min_num",
                "can_delete",
                "can_order",
                "non_form_errors",
                "forms",
                "empty_form",
                "management_form",
                "prefix",
            ],
            "additionalProperties": False,
        }


def register_widgets_in_reactivated() -> None:
    for widget_class in _widget_registry.mapping:
        if widget_class.__module__.startswith("django."):
            continue
        result = reactivated_create_schema(widget_class(), definitions_registry)
        definitions_registry.update(result.definitions)
