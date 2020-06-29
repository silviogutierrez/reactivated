import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Type,
    Union,
    get_type_hints,
)

from django import forms as django_forms
from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from . import stubs
from .models import ComputedRelation

Schema = Mapping[Any, Any]

Definitions = Mapping[str, Schema]

JSON = Any


FormError = List[str]

FormErrors = Dict[str, FormError]


class ComputedField(NamedTuple):
    name: str
    annotation: Any
    is_callable: bool

    def get_json_schema(self, definitions: Definitions) -> "Thing":
        annotation_schema = create_schema(self.annotation, definitions=definitions)

        return Thing(
            schema={**annotation_schema.schema, "callable": self.is_callable},
            definitions=annotation_schema.definitions,
        )


FieldDescriptor = Union[
    "models.Field[Any, Any]", ComputedField, ComputedRelation[Any, Any, Any]
]


class Thing(NamedTuple):
    schema: Schema
    definitions: Definitions


class ForeignKeyType:
    @classmethod
    def get_serialized_value(
        Type: Type["ForeignKeyType"], value: models.Model, schema: Thing
    ) -> JSON:
        return value.pk

    @classmethod
    def get_json_schema(
        Type: Type["ForeignKeyType"], definitions: Definitions
    ) -> "Thing":
        return Thing(
            schema={
                "type": "number",
                "serializer": "reactivated.serialization.ForeignKeyType",
            },
            definitions=definitions,
        )


class FieldType(NamedTuple):
    name: str
    label: str
    help_text: str

    # TODO: way to mark this as a custom property we define. This is just so it is
    # marked as required.
    #
    # The actual widget name is done by `form_schema`, which is kind of odd.
    # We need a better way to make a custom schema that is self contained.
    widget: Any

    @classmethod
    def get_json_schema(Type: Type["FieldType"], definitions: Definitions) -> "Thing":
        definition_name = f"{Type.__module__}.{Type.__qualname__}"

        if definition_name in definitions:
            return Thing(
                schema={"$ref": f"#/definitions/{definition_name}"},
                definitions=definitions,
            )

        schema = named_tuple_schema(Type, definitions)

        definitions = {
            **definitions,
            definition_name: {
                **schema.definitions[definition_name],
                "serializer": "field_serializer",
            },
        }

        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )


def extract_widget_context(field: django_forms.BoundField) -> Dict[str, Any]:
    """
    Previously we used a custom FormRenderer but there is *no way* to avoid
    the built in render method from piping this into `mark_safe`.

    So we monkeypatch the widget's internal renderer to return JSON directly
    without being wrapped by `mark_safe`.
    """
    field.field.widget._render = (  # type: ignore[attr-defined]
        lambda template_name, context, renderer: context
    )
    context = field.as_widget()["widget"]  # type: ignore[index]
    return context  # type: ignore[return-value]


class FormType(NamedTuple):
    name: str
    errors: Optional[FormErrors]
    fields: Dict[str, FieldType]
    iterator: List[str]
    prefix: str

    @classmethod
    def get_serialized_value(
        Type: Type["FormType"], value: django_forms.BaseForm, schema: Thing
    ) -> JSON:
        form = value

        fields = {
            field.name: FieldType(
                widget=extract_widget_context(field),
                name=field.name,
                label=str(
                    field.label
                ),  # This can be a lazy proxy, so we must call str on it.
                help_text=str(
                    field.help_text
                ),  # This can be a lazy proxy, so we must call str on it.
            )
            for field in form
        }

        return FormType(
            name=f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            errors=form.errors or None,
            fields=fields,
            iterator=list(fields.keys()),
            prefix=form.prefix or "",
        )


class FormSetType(NamedTuple):
    initial: int
    total: int
    max_num: int
    min_num: int
    can_delete: bool
    can_order: bool
    non_form_errors: List[str]

    forms: List[FormType]
    empty_form: FormType
    management_form: FormType
    prefix: str

    @classmethod
    def get_serialized_value(
        Type: Type["FormSetType"], value: stubs.BaseFormSet, schema: Thing
    ) -> JSON:
        form_set = value
        form_schema = create_schema(form_set.form, schema.definitions)

        return FormSetType(
            initial=form_set.initial_form_count(),
            total=form_set.total_form_count(),
            max_num=form_set.max_num,
            min_num=form_set.min_num,
            can_delete=form_set.can_delete,
            can_order=form_set.can_order,
            non_form_errors=form_set.non_form_errors(),
            forms=[serialize(form, form_schema) for form in form_set],
            empty_form=serialize(form_set.empty_form, form_schema),
            management_form=serialize(form_set.management_form, form_schema),
            prefix=form_set.prefix,
        )


class QuerySetType:
    @classmethod
    def get_serialized_value(
        Type: Type["QuerySetType"], value: "models.QuerySet[Any]", schema: Thing
    ) -> JSON:
        return [
            serialize(
                item,
                Thing(schema=schema.schema["items"], definitions=schema.definitions),
            )
            for item in value.all()
        ]


class Serializer(Protocol):
    def __call__(self, value: Any, schema: Thing) -> JSON:
        ...


def field_descriptor_schema(
    Type: "models.Field[Any, Any]", definitions: Definitions
) -> Thing:
    mapping = {
        models.CharField: str,
        models.BooleanField: bool,
        models.TextField: str,
        models.ForeignKey: ForeignKeyType,
        models.AutoField: int,
        models.DateField: datetime.date,
        models.DateTimeField: datetime.datetime,
        models.EmailField: str,
        models.UUIDField: str,
        models.IntegerField: int,
        models.PositiveIntegerField: int,
        models.DecimalField: str,
    }

    try:
        from django_extensions.db import fields as django_extension_fields  # type: ignore[import]

        mapping = {
            **mapping,
            django_extension_fields.ShortUUIDField: str,
        }
    except ImportError:
        pass

    mapped_type = mapping.get(Type.__class__)
    assert (
        mapped_type is not None
    ), f"Unsupported model field type {Type.__class__}. This should probably silently return None and allow a custom handler to support the field."

    FieldSchemaWithPossibleNull = (
        Union[mapped_type, None] if Type.null is True else mapped_type
    )

    return create_schema(FieldSchemaWithPossibleNull, definitions)


def generic_alias_schema(Type: stubs._GenericAlias, definitions: Definitions) -> Thing:
    subschemas: Sequence[Schema]

    if Type.__origin__ == tuple:
        *tuple_args, last_arg = Type.__args__

        if last_arg is Ellipsis:
            items_schema = create_schema(tuple_args[0], definitions)

            return Thing(
                schema={"type": "array", "items": items_schema.schema},
                definitions=items_schema.definitions,
            )

        subschemas = []

        for subtype in Type.__args__:
            subschema = create_schema(subtype, definitions=definitions)
            subschemas = [*subschemas, subschema.schema]
            definitions = {**definitions, **subschema.definitions}

        return Thing(
            schema={"type": "array", "items": subschemas}, definitions=definitions
        )
    elif Type.__origin__ == Union:
        subschemas = ()

        for subtype in Type.__args__:
            subschema = create_schema(subtype, definitions=definitions)
            subschemas = [*subschemas, subschema.schema]
            definitions = {**definitions, **subschema.definitions}

        return Thing(schema={"anyOf": subschemas}, definitions=definitions)
    elif Type.__origin__ == list:
        subschema = create_schema(Type.__args__[0], definitions=definitions)
        return Thing(
            schema={"type": "array", "items": subschema.schema},
            definitions=subschema.definitions,
        )
    elif Type.__origin__ == dict:
        subschema = create_schema(Type.__args__[1], definitions=definitions)

        return Thing(
            schema={
                "type": "object",
                "properties": {},
                "additionalProperties": subschema.schema,
            },
            definitions=subschema.definitions,
        )
    elif Type.__origin__ == Literal:
        # TODO: is a multi-Literal really this simple? Only if it's the same type.
        # Mixed types would have to be a Union of enums.

        return Thing(
            schema={"type": "string", "enum": Type.__args__}, definitions=definitions
        )

    assert False, f"Unsupported _GenericAlias {Type}"


def named_tuple_schema(Type: Any, definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    required = []
    properties = {}
    definitions = {**definitions}

    for field_name, Subtype in get_type_hints(Type).items():
        field_schema = create_schema(Subtype, definitions)
        definitions = {**definitions, **field_schema.definitions}

        required.append(field_name)
        properties[field_name] = field_schema.schema

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"},
        definitions={
            **definitions,
            definition_name: {
                "serializer": definition_name
                if callable(getattr(Type, "get_serialized_value", None))
                else None,
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required,
            },
        },
    )


def form_schema(Type: Type[django_forms.BaseForm], definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    schema = named_tuple_schema(FormType, definitions)
    """
    form_type_definition = schema.definitions[
        f"{FormType.__module__}.{FormType.__qualname__}"
    ]
    """
    field_type_definition = schema.definitions[
        f"{FieldType.__module__}.{FieldType.__qualname__}"
    ]

    error_definition = create_schema(FormError, definitions).schema

    required = []
    properties = {}
    error_properties = {}

    for field_name, SubType in Type.base_fields.items():  # type: ignore[attr-defined]
        required.append(field_name)

        SourceWidget = SubType.widget.__class__

        if SourceWidget.__module__ != "django.forms.widgets":
            SourceWidget = SubType.widget.__class__.__bases__[0]

        assert (
            SourceWidget.__module__ == "django.forms.widgets"
        ), f"Only core widgets and depth-1 inheritance widgets are currently supported. Check {SubType.widget.__class__}"

        properties[field_name] = {
            **field_type_definition,
            "properties": {
                **field_type_definition["properties"],
                "widget": {"tsType": f"widgets.{SourceWidget.__name__}"},
            },
        }
        error_properties[field_name] = error_definition

    definitions = {
        **definitions,
        definition_name: {
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": [definition_name]},
                "errors": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": error_properties,
                            "additionalProperties": False,
                        },
                        {"type": "null"},
                    ]
                },
                "fields": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                "prefix": {"type": "string"},
                "iterator": {
                    "type": "array",
                    "items": {"enum": required, "type": "string"},
                },
            },
            "serializer": "reactivated.serialization.FormType",
            "additionalProperties": False,
            "required": ["name", "prefix", "fields", "iterator", "errors"],
        },
    }

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
    )


def form_set_schema(Type: Type[stubs.BaseFormSet], definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    form_set_type_schema = create_schema(FormSetType, definitions)

    # This is gross. But Django model formsets have a special form that injects
    # the primary key after the fact, so it cannot be picked up by looping over fields
    # so we create a new form that has the primary key field at "compile" time.
    # Because we inject form names into our forms at runtime, we set the __module__
    # and __qualname__ so that the form name is still the original form's name.
    if issubclass(Type, django_forms.BaseModelFormSet):
        pk_field_name = Type.model._meta.pk.name
        FormSetForm = type(
            "FormSetForm",
            (Type.form,),
            {pk_field_name: django_forms.Field(widget=django_forms.HiddenInput)},
        )
        FormSetForm.__module__ = Type.form.__module__
        FormSetForm.__qualname__ = Type.form.__qualname__
    else:
        FormSetForm = Type.form

    form_type_schema = create_schema(FormSetForm, form_set_type_schema.definitions)

    # We use our own management form because base_fields is set dynamically
    # by Django in django.forms.formsets.
    # Because we inject form names into our forms at runtime, we set the __module__
    # and __qualname__ so that the form name is still the original form's name.
    class ManagementForm(django_forms.formsets.ManagementForm):
        base_fields: Any

    ManagementForm.base_fields = ManagementForm().base_fields
    ManagementForm.__module__ = django_forms.formsets.ManagementForm.__module__
    ManagementForm.__qualname__ = django_forms.formsets.ManagementForm.__qualname__

    management_form_schema = create_schema(ManagementForm, form_type_schema.definitions)

    form_set_type_definition = form_set_type_schema.definitions[
        f"{FormSetType.__module__}.{FormSetType.__qualname__}"
    ]

    form_type_definition = form_type_schema.definitions[
        f"{FormSetForm.__module__}.{FormSetForm.__qualname__}"
    ]

    management_form_definition = management_form_schema.definitions[
        f"{ManagementForm.__module__}.{ManagementForm.__qualname__}"
    ]

    definitions = {
        **definitions,
        definition_name: {
            **form_set_type_definition,
            "serializer": "reactivated.serialization.FormSetType",
            "properties": {
                **form_set_type_definition["properties"],
                "empty_form": form_type_definition,
                "forms": {"type": "array", "items": form_type_definition},
                "management_form": management_form_definition,
            },
        },
    }

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
    )


def create_schema(Type: Any, definitions: Definitions) -> Thing:
    if isinstance(Type, stubs._GenericAlias):
        return generic_alias_schema(Type, definitions)
    elif isinstance(Type, models.Field):
        return field_descriptor_schema(Type, definitions)
    elif Type == Any:
        return Thing(schema={}, definitions=definitions)
    elif callable(getattr(Type, "get_json_schema", None)):
        return Type.get_json_schema(definitions)  # type: ignore[no-any-return]
    elif issubclass(Type, tuple) and callable(getattr(Type, "_asdict", None)):
        return named_tuple_schema(Type, definitions)
    elif type(Type) == stubs._TypedDictMeta:
        return named_tuple_schema(Type, definitions)
    elif issubclass(Type, datetime.datetime):
        return Thing(schema={"type": "string"}, definitions={})
    elif issubclass(Type, datetime.date):
        return Thing(schema={"type": "string"}, definitions={})
    elif issubclass(Type, bool):
        return Thing(schema={"type": "boolean"}, definitions={})
    elif issubclass(Type, int):
        return Thing(schema={"type": "number"}, definitions={})
    elif issubclass(Type, float):
        return Thing(schema={"type": "number"}, definitions={})
    elif issubclass(Type, str):
        return Thing(schema={"type": "string"}, definitions={})
    elif Type is type(None):  # noqa: E721
        return Thing(schema={"type": "null"}, definitions={})
    elif issubclass(Type, django_forms.BaseForm):
        return form_schema(Type, definitions)
    elif issubclass(Type, stubs.BaseFormSet):
        return form_set_schema(Type, definitions)

    additional_schema_module: Optional[str] = getattr(
        settings, "REACTIVATED_SERIALIZATION", None
    )

    if additional_schema_module is not None:
        additional_schema: Callable[
            [Any, Definitions], Optional[Thing]
        ] = import_string(additional_schema_module)
        schema = additional_schema(Type, definitions)

        if schema is not None:
            return schema

    assert False, f"Unsupported type {Type}"


def object_serializer(value: object, schema: Thing) -> JSON:
    representation = {}

    for field_name, field_schema in schema.schema["properties"].items():
        attribute = (
            value.get(field_name, None)
            if isinstance(value, Mapping)
            else getattr(value, field_name, None)
        )

        representation[field_name] = serialize(
            attribute, Thing(schema=field_schema, definitions=schema.definitions)
        )

    additional_properties_schema = schema.schema["additionalProperties"]

    if additional_properties_schema and isinstance(value, Mapping):
        return {
            **representation,
            **{
                field_name: serialize(
                    field_value,
                    Thing(
                        schema=additional_properties_schema,
                        definitions=schema.definitions,
                    ),
                )
                for field_name, field_value in value.items()
                if field_name not in schema.schema["properties"]
            },
        }

    return representation


def array_serializer(value: Sequence[Any], schema: Thing) -> JSON:
    item_schema = schema.schema["items"]

    # For fixed tuples, though the JSON schema will actually be a list as JSON
    # has no concept of tuples.
    if isinstance(item_schema, list):
        return [
            serialize(
                item, Thing(schema=item_schema_member, definitions=schema.definitions)
            )
            for item, item_schema_member in zip(value, item_schema)
        ]

    return [
        serialize(item, Thing(schema=item_schema, definitions=schema.definitions))
        for item in value
    ]


SERIALIZERS: Dict[str, Serializer] = {
    "any": lambda value, schema: value,
    "object": object_serializer,
    "string": lambda value, schema: str(value),
    "boolean": lambda value, schema: bool(value),
    "number": lambda value, schema: float(value),
    "array": array_serializer,
    "null": lambda value, schema: None,
}


def serialize(value: Any, schema: Thing) -> JSON:
    if value is None:
        return None

    dereferenced_schema = (
        schema.definitions[schema.schema["$ref"].replace("#/definitions/", "")]
        if "$ref" in schema.schema
        else schema.schema
    )

    if dereferenced_schema.get("callable", False):
        value = value()

    if "anyOf" in dereferenced_schema:
        for any_of_schema in dereferenced_schema["anyOf"]:
            return serialize(
                value, Thing(schema=any_of_schema, definitions=schema.definitions)
            )

    serializer_path = dereferenced_schema.get("serializer", None)

    if serializer_path is not None:
        serializer: Serializer = import_string(serializer_path).get_serialized_value
    else:
        # TODO: this falls back to "any" but that feels too loose.
        # Should this be an option?
        serializer = SERIALIZERS[dereferenced_schema.get("type", "any")]

    return serializer(
        value, Thing(schema=dereferenced_schema, definitions=schema.definitions)
    )
