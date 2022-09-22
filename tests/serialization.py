from __future__ import annotations

import datetime
import enum
from typing import (
    Any,
    List,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypedDict,
    Union,
    get_type_hints,
)

import pytest
import simplejson
from django import forms as django_forms
from django.apps.registry import Apps
from django.db.models import IntegerField, Model
from django.forms.models import ModelChoiceIteratorValue
from jsonschema import validate

from reactivated import Pick
from reactivated.serialization import create_schema, serialize
from sample.server.apps.samples import forms, models


class Spam(NamedTuple):
    thing: List[str]
    again: str


class Bar(NamedTuple):
    a: str
    b: bool


class SlimEnum(enum.Enum):
    FIRST = "Ok"
    SECOND = "Great"


class ChunkyEnumMember(NamedTuple):
    is_important: bool
    title: str


class ChunkyEnum(enum.Enum):
    CHUNKY_FIRST = ChunkyEnumMember(is_important=False, title="Chunky First")
    CHUNKY_SECOND = ChunkyEnumMember(is_important=True, title="Chunky Second")


Opera = Pick[models.Opera, "name"]


class Foo(NamedTuple):
    bar: Bar
    spam: Spam

    slim_enum_type: Type[SlimEnum]
    chunky_enum_type: Type[ChunkyEnum]

    pick: Pick[models.Composer, "name", "operas.name"]
    pick_many: List[Pick[models.Composer, "name", "operas.name"]]
    pick_method: Pick[models.Opera, "name", "get_birthplace_of_composer"]
    pick_property: Pick[models.Composer, "did_live_in_more_than_one_country"]
    pick_literal: Pick[models.Composer, Literal["name", "operas.name"]]
    pick_computed_queryset: Pick[
        models.Composer, "operas_with_piano_transcriptions.name"
    ]
    pick_computed_foreign_key: Pick[models.Composer, "main_opera.name"]
    pick_computed_null_foreign_key: Pick[models.Composer, "favorite_opera.name"]
    pick_nested: Pick[models.Composer, "name", Pick["operas", Opera]]
    pick_enum: Pick[models.Continent, "hemisphere"]
    fixed_tuple_different_types: Tuple[str, int]
    fixed_tuple_same_types: Tuple[str, str]
    complex_type_we_do_not_type: Any


def convert_to_json_and_validate(instance, schema):
    def merge_all_of(json_input):
        if isinstance(json_input, dict):
            if (allOf := json_input.get("allOf")) and json_input.get(
                "_reactivated_testing_merge"
            ) is True:
                merged = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                }
                for to_merge in allOf:
                    dereferenced = (
                        schema.definitions[
                            to_merge["$ref"].replace("#/definitions/", "")
                        ]
                        if "$ref" in to_merge
                        else to_merge
                    )
                    merged["properties"].update(dereferenced["properties"])
                    merged["required"].extend(dereferenced["required"])
                return merged

            return {key: merge_all_of(value) for key, value in json_input.items()}
        elif isinstance(json_input, list):
            return [merge_all_of(value) for value in json_input]
        return json_input

    merged_definitions = merge_all_of(schema.definitions)
    converted = simplejson.loads(simplejson.dumps(instance))

    # In case the actual schema we're checking itself needs merging.
    merged_schema = merge_all_of(schema.schema)

    validate(
        instance=converted, schema={"definitions": merged_definitions, **merged_schema}
    )


@pytest.mark.django_db
def test_foreign_key_id():
    composer = models.Composer.objects.create(name="Wagner")
    opera = models.Opera.objects.create(name="Götterdämmerung", composer=composer)
    schema = create_schema(Pick[models.Opera, "composer"], {})

    assert serialize(opera, schema) == {"composer": composer.id}


@pytest.mark.django_db
def test_serialization():
    continent = models.Continent.objects.create(name="Europe")
    birth_country = models.Country.objects.create(name="Germany", continent=continent)
    other = models.Country.objects.create(name="Switzerland", continent=continent)

    composer = models.Composer.objects.create(name="Wagner")
    models.ComposerCountry.objects.create(
        composer=composer, country=birth_country, was_born=True
    )
    models.ComposerCountry.objects.create(composer=composer, country=other)

    opera = models.Opera.objects.create(name="Götterdämmerung", composer=composer)

    instance = Foo(
        bar=Bar(a="a", b=True),
        spam=Spam(thing=["one", "two", "three", "four"], again="ok"),
        slim_enum_type=SlimEnum,
        chunky_enum_type=ChunkyEnum,
        pick=composer,
        pick_many=list(models.Composer.objects.all()),
        pick_method=opera,
        pick_property=composer,
        pick_literal=composer,
        pick_computed_foreign_key=composer,
        pick_computed_null_foreign_key=composer,
        pick_computed_queryset=composer,
        pick_nested=composer,
        pick_enum=continent,
        fixed_tuple_different_types=("ok", 5),
        fixed_tuple_same_types=("alright", "again"),
        complex_type_we_do_not_type={
            "I am": "very complex",
            "because": {"I am": "nested", "ok?": []},
        },
    )
    definitions = {}
    generated_schema = create_schema(Foo, definitions)

    # TODO: flesh out type creation for Pick as well. These are currently our
    # only tests. Moreover, all other type tests are in tests/types.py.
    assert generated_schema.definitions["tests.serialization.Foo"]["properties"][
        "pick_computed_foreign_key"
    ] == {"$ref": "#/definitions/Composer_0a7e472ea2"}
    assert generated_schema.definitions["Composer_0a7e472ea2"] == {
        "additionalProperties": False,
        "properties": {
            "main_opera": {
                "additionalProperties": False,
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
                "type": "object",
            }
        },
        "required": ["main_opera"],
        "type": "object",
    }

    assert generated_schema.definitions["tests.serialization.Foo"]["properties"][
        "pick_computed_null_foreign_key"
    ] == {
        "$ref": "#/definitions/Composer_d4f73efbd8",
    }
    assert generated_schema.definitions["Composer_d4f73efbd8"] == {
        "additionalProperties": False,
        "properties": {
            "favorite_opera": {
                "anyOf": [
                    {
                        "additionalProperties": False,
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                        "type": "object",
                    },
                    {"type": "null"},
                ]
            }
        },
        "required": ["favorite_opera"],
        "type": "object",
    }

    serialized = serialize(instance, generated_schema)

    assert serialized == {
        "bar": {"a": "a", "b": True},
        "spam": {"thing": ["one", "two", "three", "four"], "again": "ok"},
        "slim_enum_type": {"FIRST": "Ok", "SECOND": "Great"},
        "chunky_enum_type": {
            "CHUNKY_FIRST": {"is_important": False, "title": "Chunky First"},
            "CHUNKY_SECOND": {"is_important": True, "title": "Chunky Second"},
        },
        "pick": {"name": composer.name, "operas": [{"name": opera.name}]},
        "pick_many": [{"name": "Wagner", "operas": [{"name": "Götterdämmerung"}]}],
        "pick_method": {
            "name": "Götterdämmerung",
            "get_birthplace_of_composer": "Germany",
        },
        "pick_property": {
            "did_live_in_more_than_one_country": True,
        },
        "pick_literal": {"name": composer.name, "operas": [{"name": opera.name}]},
        "pick_computed_foreign_key": {"main_opera": {"name": opera.name}},
        "pick_computed_null_foreign_key": {"favorite_opera": {"name": opera.name}},
        "pick_computed_queryset": {
            "operas_with_piano_transcriptions": [{"name": "Götterdämmerung"}]
        },
        "pick_nested": {"name": composer.name, "operas": [{"name": opera.name}]},
        "pick_enum": {"hemisphere": "SOUTHERN"},
        "fixed_tuple_different_types": ["ok", 5],
        "fixed_tuple_same_types": ["alright", "again"],
        "complex_type_we_do_not_type": {
            "I am": "very complex",
            "because": {"I am": "nested", "ok?": []},
        },
    }

    convert_to_json_and_validate(serialized, generated_schema)


@pytest.mark.skip
def test_form():
    generated_schema = create_schema(forms.OperaForm, {})
    form = forms.OperaForm()
    serialized_form = serialize(form, generated_schema)
    convert_to_json_and_validate(serialized_form, generated_schema)

    form_with_errors = forms.OperaForm({})
    form_with_errors.is_valid()
    serialized_form = serialize(form_with_errors, generated_schema)
    assert "name" in serialized_form.errors
    convert_to_json_and_validate(serialized_form, generated_schema)


@pytest.mark.skip
def test_widget_inheritance():
    class WidgetMixin:
        pass

    class ChildWidget(WidgetMixin, django_forms.TextInput):
        pass

    class FormWithChildWidget(django_forms.Form):
        my_field = django_forms.CharField(widget=ChildWidget)

    # No error, depth-1 inheritance.
    create_schema(FormWithChildWidget, {})

    class GrandchildWidget(ChildWidget):
        pass

    class FormWithGrandchildWidget(django_forms.Form):
        my_field = django_forms.CharField(widget=GrandchildWidget)

    with pytest.raises(AssertionError, match="depth-1"):
        create_schema(FormWithGrandchildWidget, {})


@pytest.mark.skip
def test_custom_widget():
    class CustomWidget(django_forms.Select):
        reactivated_widget = "foo"

    class CustomForm(django_forms.Form):
        field = django_forms.CharField(widget=CustomWidget)

    generated_schema = create_schema(CustomForm, {})
    form = CustomForm()
    serialized_form = serialize(form, generated_schema)
    convert_to_json_and_validate(serialized_form, generated_schema)
    assert serialized_form.fields["field"].widget["template_name"] == "foo"


def test_subwidget():
    class SubwidgetForm(django_forms.Form):
        date_field = django_forms.DateField(widget=django_forms.SelectDateWidget)

    generated_schema = create_schema(SubwidgetForm, {})
    form = SubwidgetForm()
    serialized_form = serialize(form, generated_schema)
    convert_to_json_and_validate(serialized_form, generated_schema)


@pytest.mark.django_db
def test_form_with_model_choice_iterator_value():
    models.Country.objects.create(
        name="USA",
        continent=models.Continent.objects.create(
            name="America", hemisphere="NORTHERN"
        ),
    )
    iterator = (
        forms.ComposerForm()
        .fields["countries"]
        .widget.optgroups("countries", "")[0][1][0]["value"]
    )

    assert isinstance(iterator, ModelChoiceIteratorValue)

    generated_schema = create_schema(forms.ComposerForm, {})
    form = forms.ComposerForm()
    serialized_form = serialize(form, generated_schema)

    convert_to_json_and_validate(serialized_form, generated_schema)
    assert serialized_form["fields"]["countries"]["widget"]["optgroups"][0][1][0][
        "value"
    ] == str(iterator.value)


@pytest.mark.django_db
def test_form_set():
    generated_schema = create_schema(forms.OperaFormSet, {})
    form_set = forms.OperaFormSet()
    serialized_form_set = serialize(form_set, generated_schema)
    convert_to_json_and_validate(serialized_form_set, generated_schema)

    form_set_with_errors = forms.OperaFormSet(
        {"form-TOTAL_FORMS": 20, "form-INITIAL_FORMS": 0}
    )
    form_set_with_errors.is_valid()
    serialized_form_set = serialize(form_set_with_errors, generated_schema)
    assert "name" in serialized_form_set["forms"][0]["errors"]
    convert_to_json_and_validate(serialized_form_set, generated_schema)


@pytest.mark.skip
def test_typed_choices_non_enum(settings):
    settings.INSTALLED_APPS = ["tests.serialization"]
    test_apps = Apps(settings.INSTALLED_APPS)

    class TestModel(Model):
        non_enum_typed_field = IntegerField(choices=((0, "Zero"), (1, "One")))

        class Meta:
            apps = test_apps

    class TestForm(django_forms.ModelForm):
        class Meta:
            model = TestModel
            fields = "__all__"

    generated_schema = create_schema(TestForm, {})
    assert generated_schema.definitions[
        "tests.serialization.test_typed_choices_non_enum.<locals>.TestForm"
    ]["properties"]["fields"]["properties"]["non_enum_typed_field"]["properties"][
        "widget"
    ] == {
        "tsType": "widgets.Select"
    }


def test_override_pick_types(settings, snapshot):
    settings.INSTALLED_APPS = ["tests.serialization"]
    test_apps = Apps(settings.INSTALLED_APPS)

    class TestModel(Model):
        forced_nullable: Optional[int] = IntegerField()
        forced_non_nullable: int = IntegerField(null=True)
        forced_none: None = IntegerField()

        class Meta:
            apps = test_apps

    Picked = Pick[TestModel, "forced_nullable", "forced_non_nullable", "forced_none"]
    schema = create_schema(Picked, {})
    assert schema.schema == {
        "$ref": "#/definitions/test_override_pick_types.<locals>.TestModel_fdae93dc88",
    }
    assert (
        schema.definitions["test_override_pick_types.<locals>.TestModel_fdae93dc88"]
        == snapshot
    )


def test_deferred_evaluation_of_types(settings):
    settings.INSTALLED_APPS = ["tests.serialization"]
    test_apps = Apps(settings.INSTALLED_APPS)

    class TestModel(Model):
        deferred_field: DoesNotExist = IntegerField()

        @property
        def bar(self) -> DoesNotExist:
            assert False

        @classmethod
        def resolve_type_hints(cls):
            return {
                "DoesNotExist": bool,
            }

        class Meta:
            apps = test_apps

    Picked = Pick[TestModel, "bar", "deferred_field"]

    schema = create_schema(Picked, {})

    assert schema.schema == {
        "$ref": "#/definitions/test_deferred_evaluation_of_types.<locals>.TestModel_53f578dd7a"
    }
    assert schema.definitions[
        "test_deferred_evaluation_of_types.<locals>.TestModel_53f578dd7a"
    ] == {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "bar": {
                "type": "boolean",
                "serializer": "reactivated.serialization.ComputedField",
            },
            "deferred_field": {"type": "boolean"},
        },
        "required": ["bar", "deferred_field"],
    }


def test_pick_reverse_relationship():
    with pytest.raises(AssertionError, match="reverse relationships"):
        assert create_schema(Pick[models.Composer, "operas"], {})
    assert create_schema(Pick[models.Composer, "operas.name"], {})


def test_form_and_fields(snapshot):
    date = datetime.date(2015, 1, 1)
    Form = forms.StoryboardForm

    instance = Form(initial={"date_field": date, "boolean_field": True})

    schema = create_schema(Form, {})
    serialized = serialize(instance, schema)

    assert serialized["fields"]["char_field"] == {
        "help_text": None,
        "label": "Char field",
        "name": "char_field",
        "widget": {
            "tag": "django.forms.widgets.TextInput",
            "attrs": {
                # "disabled": None,
                "id": "id_char_field",
                # "maxlength": None,
                # "placeholder": None,
                "required": True,
            },
            "is_hidden": False,
            "name": "char_field",
            "required": True,
            "template_name": "django/forms/widgets/text.html",
            "type": "text",
            "value": None,
        },
    }
    field_schema = create_schema(Form.base_fields["char_field"], schema.definitions)
    convert_to_json_and_validate(serialized["fields"]["char_field"], field_schema)

    assert serialized["fields"]["integer_field"] == {
        "help_text": None,
        "label": "Integer field",
        "name": "integer_field",
        "widget": {
            "tag": "django.forms.widgets.NumberInput",
            "attrs": {
                # "disabled": None,
                "id": "id_integer_field",
                # "placeholder": None,
                "required": True,
                # "step": None,
            },
            "is_hidden": False,
            "name": "integer_field",
            "required": True,
            "template_name": "django/forms/widgets/number.html",
            "type": "number",
            "value": None,
        },
    }
    field_schema = create_schema(Form.base_fields["integer_field"], schema.definitions)
    convert_to_json_and_validate(serialized["fields"]["integer_field"], field_schema)

    assert serialized["fields"]["date_field"] == snapshot

    field_schema = create_schema(Form.base_fields["date_field"], schema.definitions)
    convert_to_json_and_validate(serialized["fields"]["date_field"], field_schema)

    assert serialized["fields"]["date_time_field"] == snapshot
    field_schema = create_schema(
        Form.base_fields["date_time_field"], schema.definitions
    )
    convert_to_json_and_validate(serialized["fields"]["date_time_field"], field_schema)

    assert serialized["fields"]["boolean_field"] == snapshot
    field_schema = create_schema(Form.base_fields["boolean_field"], schema.definitions)
    convert_to_json_and_validate(serialized["fields"]["boolean_field"], field_schema)


NamedPick = Pick[models.Opera, "name"]


class Holder:
    unnamed_pick1: Pick[models.Opera, "id", "name"]
    unnamed_pick2: Pick[models.Opera, "name", "id"]


def test_pick_name_and_deduplication(settings):
    # Note we purposely set the app name to the parent dir so that this file is
    # treated as a file inside the app tests.
    settings.INSTALLED_APPS = ["tests"]
    assert NamedPick.get_name() == "tests.serialization.Opera"
    assert get_type_hints(Holder)["unnamed_pick1"].get_name() is None
    assert (
        get_type_hints(Holder)["unnamed_pick1"].get_auto_name()
        == get_type_hints(Holder)["unnamed_pick2"].get_auto_name()
    )


def test_tagged_union():
    class One(TypedDict):
        tag: Literal["one"]
        something: int

    class Two(TypedDict):
        tag: Literal["two"]
        another: bool

    InvalidUnion = Union[One, Two, int]

    with pytest.raises(AssertionError, match="must have only"):
        create_schema(InvalidUnion, {})

    TaggedUnion = Union[One, Two, None]
    schema = create_schema(TaggedUnion, {})
    assert serialize({"tag": "one", "something": 5}, schema) == {
        "tag": "one",
        "something": 5,
    }

    assert serialize({"tag": "two", "another": True}, schema) == {
        "tag": "two",
        "another": True,
    }

    assert serialize(None, schema) is None


class Parent(NamedTuple):
    foo: str


class Child(Parent):
    pass


def test_union_with_inheritance():
    schema = create_schema(Union[Parent, bool, int], {})
    assert serialize(5, schema) == 5
    assert serialize(True, schema) is True
    assert serialize(Parent(foo="one"), schema)


def test_simple_union():
    schema = create_schema(
        Union[datetime.date, List[str], Tuple[int, str], int, str, bool, None], {}
    )
    # assert schema.schema == {'anyOf': [{'type': 'string'}, {'type': 'string'}, {'type': 'null'}]}
    assert serialize(None, schema) is None
    assert serialize(10, schema) == 10.0
    assert serialize(datetime.date(2022, 1, 2), schema) == "2022-01-02"
    assert serialize(["1", "2", "3"], schema) == ["1", "2", "3"]
    assert serialize((5, "hello"), schema) == [5, "hello"]
    assert serialize(True, schema) is True


def test_pick_union():
    schema = create_schema(Union[List[int], NamedPick, int, None], {})
    assert serialize(models.Opera(name="My Opera"), schema) == {"name": "My Opera"}
    assert serialize(10, schema) == 10.0
    assert serialize(None, schema) is None
    assert serialize([1, 2, 3], schema) == [1, 2, 3]
