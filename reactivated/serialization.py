import datetime
import enum
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
    Tuple,
    Type,
    Union,
    get_type_hints,
)

from django import forms as django_forms
from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from . import fields, stubs
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

    @classmethod
    def get_serialized_value(
        Type: Type["ComputedField"], value: Any, schema: "Thing"
    ) -> JSON:
        called_value = value() if callable(value) is True else value
        called_value_schema = {**schema.schema}
        called_value_schema.pop("serializer")

        return serialize(
            called_value,
            Thing(schema=called_value_schema, definitions=schema.definitions),
        )

    def get_json_schema(self, definitions: Definitions) -> "Thing":
        annotation_schema = create_schema(self.annotation, definitions=definitions)

        return Thing(
            schema={
                **annotation_schema.schema,
                "serializer": "reactivated.serialization.ComputedField",
            },
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


class OptgroupMember(NamedTuple):
    name: str
    value: Union[str, int, bool, None]
    label: str
    selected: bool


Optgroup = Tuple[None, Tuple[OptgroupMember], int]

"""
type Optgroup = [
    null,
    [
        {
            name: string;
            // value: string|number|boolean|null;
            value: string | number | boolean | null;
            label: string;
            selected: boolean;
        },
    ],
    number,
];
"""


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
    original_render = field.field.widget._render  # type: ignore[attr-defined]
    field.field.widget._render = (  # type: ignore[attr-defined]
        lambda template_name, context, renderer: context
    )
    widget = field.as_widget()
    context: Any = widget["widget"]  # type: ignore[index]
    context["template_name"] = getattr(
        field.field.widget, "reactivated_widget", context["template_name"]
    )
    optgroups = context.get("optgroups", None)

    # This is our first foray into properly serializing widgets using the
    # serialization framework.
    #
    # Eventually all widgets can be serialized this way and the frontend widget
    # types can disappear and be generated from the code here.
    if optgroups is not None:
        optgroup_schema = create_schema(Optgroup, {})  # type: ignore[misc]
        context["optgroups"] = [
            serialize(optgroup, optgroup_schema) for optgroup in optgroups
        ]

    field.field.widget._render = original_render  # type: ignore[attr-defined]

    return context  # type: ignore[no-any-return]


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
        models.CharField: lambda field: str,
        models.BooleanField: lambda field: bool,
        models.TextField: lambda field: str,
        models.ForeignKey: lambda field: ForeignKeyType,
        models.AutoField: lambda field: int,
        models.DateField: lambda field: datetime.date,
        models.DateTimeField: lambda field: datetime.datetime,
        models.EmailField: lambda field: str,
        models.UUIDField: lambda field: str,
        models.IntegerField: lambda field: int,
        models.PositiveIntegerField: lambda field: int,
        models.DecimalField: lambda field: str,
        fields.EnumField: lambda field: field.enum,
    }

    try:
        from django_extensions.db import fields as django_extension_fields  # type: ignore[import]

        mapping = {
            **mapping,
            django_extension_fields.ShortUUIDField: lambda field: str,
        }
    except ImportError:
        pass

    mapped_type_callable = mapping.get(Type.__class__)
    assert (
        mapped_type_callable is not None
    ), f"Unsupported model field type {Type.__class__}. This should probably silently return None and allow a custom handler to support the field."

    mapped_type = mapped_type_callable(Type)  # type: ignore[no-untyped-call]

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
    elif Type.__origin__ == type and issubclass(
        (enum_type := Type.__args__[0]), enum.Enum
    ):
        return enum_type_schema(enum_type, definitions)

    assert False, f"Unsupported _GenericAlias {Type}"


class EnumValueType(NamedTuple):
    @classmethod
    def get_serialized_value(
        Type: Type["EnumValueType"], value: enum.Enum, schema: Thing
    ) -> JSON:
        enum_value = value.value
        enum_value_schema = {**schema.schema}
        enum_value_schema.pop("serializer")

        return serialize(
            enum_value, Thing(schema=enum_value_schema, definitions=schema.definitions)
        )


class EnumMemberType(NamedTuple):
    @classmethod
    def get_serialized_value(
        Type: Type["EnumMemberType"], value: enum.Enum, schema: Thing
    ) -> JSON:
        member = value.name
        return serialize(value.name, create_schema(type(member), schema.definitions))


def enum_type_schema(Type: Type[enum.Enum], definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}EnumType"

    if definition_name in definitions:
        return Thing(
            schema={"$ref": f"#/definitions/{definition_name}"}, definitions=definitions
        )

    required = []
    properties = {}
    definitions = {**definitions}

    for member in Type:
        member_schema = create_schema(type(member.value), definitions)
        definitions = {**definitions, **member_schema.definitions}

        required.append(member.name)
        properties[member.name] = {
            **member_schema.schema,
            "serializer": "reactivated.serialization.EnumValueType",
        }

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"},
        definitions={
            **definitions,
            definition_name: {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required,
            },
        },
    )

    # call serialize on yourself, but with the value of the enum. Try doing that for callable too.
    # Basically set a custom serializer then in the custom serliazer, you just access value.value and call serialzie again with the same schema.
    # For callable, call value() then pass the same schema down.
    # Beautiful.

    # named_tuple_fields = [
    #     (member_name, type(member_value.value)) for member_name, member_value in enum_type._member_map_.items()
    # ]
    # EnumNamedTuple = NamedTuple('EnumNamedTuple', named_tuple_fields)
    # EnumNamedTuple.__qualname__ = enum_type.__qualname__
    # EnumNamedTuple.__module__ = enum_type.__module__


def enum_schema(Type: Type[enum.Enum], definitions: Definitions) -> Thing:
    definition_name = f"{Type.__module__}.{Type.__qualname__}"

    return Thing(
        schema={"$ref": f"#/definitions/{definition_name}"},
        definitions={
            **definitions,
            definition_name: {
                "type": "string",
                "enum": list(member.name for member in Type),
                "serializer": "reactivated.serialization.EnumMemberType",
            },
        },
    )


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

    for field_name in dir(Type):
        if field_name in properties:
            continue

        possible_method_or_property = getattr(Type, field_name)

        if isinstance(possible_method_or_property, property):
            annotations = get_type_hints(possible_method_or_property.fget)
            field_schema = create_schema(annotations["return"], definitions)
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

        ts_type = f"widgets.{SourceWidget.__name__}"

        # Special treatment to register global Enum types and reference them
        # through `tsType`

        # Tightly coupled, for now. Can likely be improved once we have proper
        # widget schema generation.
        if isinstance(SubType, django_forms.TypedChoiceField) and (
            choices := list(SubType.choices)
        ):
            # The internal _coerce method checks empty values for us too.
            choice = SubType._coerce(choices[0][0])  # type: ignore

            choice_schema, definitions = create_schema(type(choice), definitions)

            if (ref := choice_schema.get("$ref", None)) :
                generic_name = "".join(
                    part.capitalize()
                    for part in ref.replace("#/definitions/", "").split(".")
                )

                from . import global_types

                global_types[generic_name] = choice_schema  # type: ignore[assignment]

                ts_type = f'widgets.{SourceWidget.__name__}<Types["globals"]["{generic_name}"]>'

        properties[field_name] = {
            **field_type_definition,
            "properties": {
                **field_type_definition["properties"],
                "widget": {"tsType": ts_type},
            },
        }
        error_properties[field_name] = error_definition

    iterator = (
        {"type": "array", "items": {"enum": required, "type": "string"},}
        if len(required) > 0
        else {"type": "array", "items": []}
    )

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
                "iterator": iterator,
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

    # Everything the child form added needs to be part of our global definitions
    # now.
    definitions = form_type_schema.definitions

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
    elif issubclass(Type, enum.Enum):
        return enum_schema(Type, definitions)

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

    serializer: Serializer
    serializer_path = schema.schema.get("serializer", None)

    # A custom serializer gets priority over anyOf and $ref.
    # Technically anyOf and $ref could themselves be serializers of sorts. But
    # callables need both a serializer to call the value and then a serializer
    # to loop over the anyOf. Not sure how to abstract this out. So anyOf
    # remains a higher-order construct. Same for $ref.
    if serializer_path is not None:
        serializer = import_string(serializer_path).get_serialized_value
        return serializer(value, schema,)
    elif "$ref" in schema.schema:
        dereferenced_schema = schema.definitions[
            schema.schema["$ref"].replace("#/definitions/", "")
        ]

        return serialize(
            value, Thing(schema=dereferenced_schema, definitions=schema.definitions)
        )
    elif "anyOf" in schema.schema:
        for any_of_schema in schema.schema["anyOf"]:
            return serialize(
                value, Thing(schema=any_of_schema, definitions=schema.definitions)
            )

    # TODO: this falls back to "any" but that feels too loose.
    # Should this be an option?
    serializer = SERIALIZERS[schema.schema.get("type", "any")]

    return serializer(value, schema,)
