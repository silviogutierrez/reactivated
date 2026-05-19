from __future__ import annotations

import datetime
import decimal
import enum
import inspect
import json
import logging
from types import NoneType, UnionType
from typing import Any, Callable, Literal, TypeVar, cast, get_origin, get_type_hints

from pydantic import EmailStr, Field, SecretStr, model_validator
from pydantic_core import PydanticUndefined
from reactivated.utils import ClassLookupDict

from .utils import module_name_to_app_name

logger = logging.getLogger("django.server")


WidgetType = Literal[
    "text",
    "password",
    "email",
    "textarea",
    "select",
    "boolean",
    "number",
    "decimal",
    "date",
    "duration",
    "energy",
    "length",
    "weight",
    "percent",
    "markdown",
    "multiplier",
    "range",
]


def FormField(
    default: Any = ...,
    *,
    widget: WidgetType | None = None,
    options: tuple[tuple[str | bool, str], ...] | None = None,
    label: str | None = None,
    placeholder: str | None = None,
    required: bool | None = None,
    read_only: bool | None = None,
) -> Any:
    """
    Define a form field with optional metadata for schema generation.

    read_only: When True, the field appears in the form schema (for display) but:
      - Defaults to None in the JSON schema, so it's not required in requests
      - Server ignores any client-provided value and sets it to None
      - Frontend must provide initial values via useAutoPform's second argument
      - Field type must be Optional (e.g., str | None)
    """
    # Read-only fields default to None so they're not required in the JSON schema
    effective_default = None if read_only is True and default is ... else default
    return Field(
        default=effective_default,
        json_schema_extra={
            "form_widget": widget,
            "form_options": cast(Any, options),
            "form_label": label,
            "form_placeholder": placeholder,
            "form_required": required,
            "form_read_only": read_only,
        },
    )


TForm = TypeVar("TForm", bound=type)


def form(
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> Callable[[TForm], TForm]:
    if include is not None and exclude is not None:
        raise ValueError("Cannot specify both 'include' and 'exclude'")

    def inner(cls: TForm) -> TForm:
        hints = get_type_hints(cls, include_extras=True)
        valid_fields = {name for name in hints if not name.startswith("_")}

        if include is not None:
            invalid = set(include) - valid_fields
            if invalid:
                raise ValueError(
                    f"Invalid field names in 'include': {invalid}. "
                    f"Valid fields: {valid_fields}"
                )

        if exclude is not None:
            invalid = set(exclude) - valid_fields
            if invalid:
                raise ValueError(
                    f"Invalid field names in 'exclude': {invalid}. "
                    f"Valid fields: {valid_fields}"
                )

        # Determine which fields are required/disabled/optional for pre-validation
        model_fields = getattr(cls, "model_fields", {})
        required_fields: list[str] = []
        disabled_fields: list[str] = []
        optional_fields: list[str] = []

        for field_name, field_type in hints.items():
            if field_name.startswith("_"):
                continue

            extra = model_fields.get(field_name)
            form_required: bool | None = None
            form_read_only: bool | None = None
            if extra is not None and isinstance(extra.json_schema_extra, dict):
                form_required = extra.json_schema_extra.get("form_required")
                form_read_only = extra.json_schema_extra.get("form_read_only")

            # Track read-only fields - they get stripped from input
            if form_read_only is True:
                if not _is_optional_type(field_type):
                    raise ValueError(
                        f"Read-only field '{field_name}' must be Optional (allow None). "
                        f"Use: {field_name}: {field_type} | None = FormField(read_only=True)"
                    )
                disabled_fields.append(field_name)
                continue  # Read-only fields are never required

            # Fields are required by default unless explicitly marked required=False
            if form_required is False:
                optional_fields.append(field_name)
            else:
                required_fields.append(field_name)

        # Create subclass with pre-validator for required fields
        class ValidatedForm(cls):  # type: ignore[valid-type,misc]
            @model_validator(mode="before")
            @classmethod
            def _check_required_fields(cls, data: Any) -> Any:
                if not isinstance(data, dict):
                    return data
                # Ignore client data for read-only fields, set to None
                for field_name in disabled_fields:
                    data[field_name] = None
                # Set missing optional fields to None
                for field_name in optional_fields:
                    if field_name not in data:
                        data[field_name] = None
                # Remove empty required fields so Pydantic reports them as "missing"
                # with correct loc - we map "missing" to "This field is required" message
                # Only treat empty strings as missing - preserve False, 0, and other falsy values
                for field_name in required_fields:
                    if field_name in data and data[field_name] == "":
                        del data[field_name]
                return data

        # Preserve class identity
        ValidatedForm.__name__ = cls.__name__
        ValidatedForm.__qualname__ = cls.__qualname__
        ValidatedForm.__module__ = cls.__module__

        ValidatedForm._form_include = include
        ValidatedForm._form_exclude = exclude

        form_registry.append(ValidatedForm)
        return ValidatedForm  # type: ignore[return-value]

    return inner


form_registry: list[type] = []


def _is_optional_type(field_type: Any) -> bool:
    """Check if a type annotation is Optional (allows None)."""
    if isinstance(field_type, UnionType):
        return NoneType in field_type.__args__
    if hasattr(field_type, "__origin__") and field_type.__origin__ is UnionType:
        return NoneType in field_type.__args__
    return False


def _humanize_field_name(name: str) -> str:
    return name.replace("_", " ").capitalize()


WIDGET_TYPE_MAPPING = ClassLookupDict(
    {
        bool: "boolean",
        int: "number",
        float: "decimal",
        decimal.Decimal: "decimal",
        datetime.date: "date",
        datetime.datetime: "date",
        datetime.timedelta: "duration",
        EmailStr: "email",
        SecretStr: "password",
        str: "text",
    }
)


def _get_widget_type_from_python_type(python_type: Any) -> WidgetType:
    if isinstance(python_type, UnionType):
        non_none_args = [a for a in python_type.__args__ if a is not NoneType]
        if len(non_none_args) == 1:
            python_type = non_none_args[0]

    if get_origin(python_type) is Literal:
        return "select"

    if inspect.isclass(python_type) and issubclass(python_type, enum.Enum):
        return "select"

    try:
        return cast(WidgetType, WIDGET_TYPE_MAPPING[python_type])
    except (KeyError, TypeError):
        return "text"


def _get_enum_options(python_type: Any) -> list[tuple[str, str]]:
    if get_origin(python_type) is Literal:
        args = python_type.__args__
        return [(str(arg), str(arg)) for arg in args]

    if inspect.isclass(python_type) and issubclass(python_type, enum.Enum):
        return [(member.name, str(member.value)) for member in python_type]

    return []


def _get_default_value(
    python_type: Any,
    widget_type: str,
    default: Any,
    *,
    is_required: bool = False,
    options: list[tuple[Any, str]] | None = None,
) -> Any:
    # Widget types that use string values in TypeScript (not number).
    string_valued_widgets = {
        "decimal",
        "weight",
        "length",
        "energy",
        "percent",
        "multiplier",
        "range",
    }

    if default is not inspect.Parameter.empty:
        if isinstance(default, enum.Enum):
            return default.name
        # Stringify numeric defaults for string-valued widget types only.
        # "number" and "duration" use number values in TypeScript.
        if (
            isinstance(default, (int, float, decimal.Decimal))
            and not isinstance(default, bool)
            and widget_type in string_valued_widgets
        ):
            return str(default)
        return default

    if widget_type == "boolean":
        return False
    if widget_type in (
        "number",
        "decimal",
        "date",
        "duration",
        "energy",
        "length",
        "weight",
        "percent",
        "multiplier",
        "range",
    ):
        return None
    if widget_type == "select":
        if is_required and options:
            return options[0][0]
        return None

    return ""


def get_form_schema(form_cls: type) -> dict[str, Any]:
    hints = get_type_hints(form_cls, include_extras=True)
    fields: dict[str, dict[str, Any]] = {}
    defaults: dict[str, Any] = {}
    iterator: list[str] = []

    include: list[str] | None = getattr(form_cls, "_form_include", None)
    exclude: list[str] | None = getattr(form_cls, "_form_exclude", None)

    model_fields = getattr(form_cls, "model_fields", {})

    for field_name, field_type in hints.items():
        if field_name.startswith("_"):
            continue

        if include is not None and field_name not in include:
            continue
        if exclude is not None and field_name in exclude:
            continue

        # Get base type (unwrap Annotated if present)
        base_type = field_type
        if hasattr(field_type, "__origin__") and hasattr(field_type, "__metadata__"):
            base_type = field_type.__origin__

        # Get form metadata from json_schema_extra
        form_widget: str | None = None
        form_options: tuple[tuple[Any, str], ...] | None = None
        form_label: str | None = None
        form_placeholder: str | None = None
        form_required: bool | None = None
        form_read_only: bool | None = None

        if field_name in model_fields:
            model_field = model_fields[field_name]
            extra = model_field.json_schema_extra
            if isinstance(extra, dict):
                form_widget = extra.get("form_widget")
                form_options = extra.get("form_options")
                form_label = extra.get("form_label")
                form_placeholder = extra.get("form_placeholder")
                form_required = extra.get("form_required")
                form_read_only = extra.get("form_read_only")

        # Determine widget type
        # If options are provided, it's always a select
        if form_options is not None:
            widget_type = "select"
        elif form_widget:
            widget_type = form_widget
        else:
            widget_type = _get_widget_type_from_python_type(base_type)

        # Get default value
        default_value: Any = inspect.Parameter.empty
        if field_name in model_fields:
            model_field = model_fields[field_name]
            if model_field.default is not PydanticUndefined:
                default_value = model_field.default
            elif model_field.default_factory is not None:
                default_value = model_field.default_factory()

        # Fields are required by default unless explicitly marked required=False
        is_required = form_required is not False

        # Build field definition
        field_def: dict[str, Any] = {
            "type": widget_type,
        }

        if form_widget:
            field_def["widget"] = form_widget

        field_def["readOnly"] = form_read_only is True

        # Always add label - use explicit label or humanize field name
        field_def["label"] = form_label or _humanize_field_name(field_name)

        if form_placeholder:
            field_def["placeholder"] = form_placeholder

        # Add options for select fields
        options: list[tuple[Any, str]] = []
        if widget_type == "select":
            if form_options is not None:
                # Use explicitly provided options
                options = list(form_options)
            else:
                # Extract options from Literal/Enum type
                actual_type = base_type
                if (
                    hasattr(base_type, "__origin__")
                    and base_type.__origin__ is UnionType
                ):
                    non_none = [a for a in base_type.__args__ if a is not NoneType]
                    if non_none:
                        actual_type = non_none[0]
                options = _get_enum_options(actual_type)

            if options:
                field_def["options"] = options

        # For select fields with an empty string option, always mark as required
        # in schema because "" is a valid value (not null). This ensures TypeScript
        # uses the non-nullable value type (TEnum instead of TEnum | null).
        schema_required = is_required
        if widget_type == "select" and options and any(opt[0] == "" for opt in options):
            schema_required = True

        if schema_required:
            field_def["required"] = True

        fields[field_name] = field_def
        iterator.append(field_name)

        defaults[field_name] = _get_default_value(
            base_type,
            widget_type,
            default_value,
            is_required=schema_required,
            options=options,
        )

    return {"fields": fields, "defaults": defaults, "iterator": iterator}


def generate_forms_export() -> str:
    if not form_registry:
        return "\nexport const forms = {} as const;\n\nexport interface forms {}\n"

    forms_dict: dict[str, dict[str, Any]] = {}

    for form_cls in form_registry:
        app_name = module_name_to_app_name(form_cls.__module__)
        form_name = (
            f"{app_name}.{form_cls.__qualname__}"
            if app_name
            else f"{form_cls.__module__}.{form_cls.__qualname__}"
        )
        try:
            form_schema = get_form_schema(form_cls)
            forms_dict[form_name] = form_schema
        except Exception as e:
            logger.warning(f"Failed to generate form schema for {form_name}: {e}")
            continue

    forms_json = json.dumps(forms_dict, indent=4)

    # Generate interface that parallels the const for proper type inference
    interface_members = "\n".join(
        f'    "{form_name}": typeof forms["{form_name}"];'
        for form_name in forms_dict.keys()
    )
    interface_def = f"export interface forms {{\n{interface_members}\n}}"

    return f"\nexport const forms = {forms_json} as const;\n\n{interface_def}\n"
