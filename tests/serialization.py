from __future__ import annotations

import datetime
import enum
from typing import Any, List, Literal, NamedTuple, Optional, Tuple, Type, get_type_hints

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
    import pprint

    pprint.pprint(generated_schema.dereference())
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


def test_override_pick_types(settings):
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
    assert schema.definitions[
        "test_override_pick_types.<locals>.TestModel_fdae93dc88"
    ] == {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "forced_nullable": {"anyOf": [{"type": "number"}, {"type": "null"}]},
            "forced_non_nullable": {"type": "number"},
            "forced_none": {"type": "null"},
        },
        "required": ["forced_nullable", "forced_non_nullable", "forced_none"],
    }


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


def test_form_and_fields():
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

    assert serialized["fields"]["date_field"] == {
        "help_text": None,
        "label": "Date field",
        "name": "date_field",
        "widget": {
            "attrs": {
                # "disabled": None,
                "id": "id_date_field",
                # "placeholder": None,
                "required": True,
            },
            "is_hidden": False,
            "name": "date_field",
            "required": True,
            "subwidgets": [
                {
                    "attrs": {
                        # "disabled": None,
                        "id": "id_date_field_month",
                        # "placeholder": None,
                        "required": True,
                    },
                    "is_hidden": False,
                    "name": "date_field_month",
                    "optgroups": [
                        [
                            None,
                            [
                                {
                                    "label": "January",
                                    "name": "date_field_month",
                                    "selected": True,
                                    "value": "1",
                                }
                            ],
                            0.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "February",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "2",
                                }
                            ],
                            1.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "March",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "3",
                                }
                            ],
                            2.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "April",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "4",
                                }
                            ],
                            3.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "May",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "5",
                                }
                            ],
                            4.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "June",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "6",
                                }
                            ],
                            5.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "July",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "7",
                                }
                            ],
                            6.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "August",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "8",
                                }
                            ],
                            7.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "September",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "9",
                                }
                            ],
                            8.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "October",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "10",
                                }
                            ],
                            9.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "November",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "11",
                                }
                            ],
                            10.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "December",
                                    "name": "date_field_month",
                                    "selected": False,
                                    "value": "12",
                                }
                            ],
                            11.0,
                        ],
                    ],
                    "required": False,
                    "tag": "django.forms.widgets.Select",
                    "template_name": "django/forms/widgets/select.html",
                    "value": "1",
                },
                {
                    "attrs": {
                        # "disabled": None,
                        "id": "id_date_field_day",
                        # "placeholder": None,
                        "required": True,
                    },
                    "is_hidden": False,
                    "name": "date_field_day",
                    "optgroups": [
                        [
                            None,
                            [
                                {
                                    "label": "1",
                                    "name": "date_field_day",
                                    "selected": True,
                                    "value": "1",
                                }
                            ],
                            0.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "2",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "2",
                                }
                            ],
                            1.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "3",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "3",
                                }
                            ],
                            2.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "4",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "4",
                                }
                            ],
                            3.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "5",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "5",
                                }
                            ],
                            4.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "6",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "6",
                                }
                            ],
                            5.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "7",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "7",
                                }
                            ],
                            6.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "8",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "8",
                                }
                            ],
                            7.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "9",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "9",
                                }
                            ],
                            8.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "10",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "10",
                                }
                            ],
                            9.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "11",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "11",
                                }
                            ],
                            10.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "12",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "12",
                                }
                            ],
                            11.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "13",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "13",
                                }
                            ],
                            12.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "14",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "14",
                                }
                            ],
                            13.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "15",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "15",
                                }
                            ],
                            14.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "16",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "16",
                                }
                            ],
                            15.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "17",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "17",
                                }
                            ],
                            16.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "18",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "18",
                                }
                            ],
                            17.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "19",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "19",
                                }
                            ],
                            18.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "20",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "20",
                                }
                            ],
                            19.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "21",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "21",
                                }
                            ],
                            20.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "22",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "22",
                                }
                            ],
                            21.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "23",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "23",
                                }
                            ],
                            22.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "24",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "24",
                                }
                            ],
                            23.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "25",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "25",
                                }
                            ],
                            24.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "26",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "26",
                                }
                            ],
                            25.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "27",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "27",
                                }
                            ],
                            26.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "28",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "28",
                                }
                            ],
                            27.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "29",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "29",
                                }
                            ],
                            28.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "30",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "30",
                                }
                            ],
                            29.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "31",
                                    "name": "date_field_day",
                                    "selected": False,
                                    "value": "31",
                                }
                            ],
                            30.0,
                        ],
                    ],
                    "required": False,
                    "tag": "django.forms.widgets.Select",
                    "template_name": "django/forms/widgets/select.html",
                    "value": "1",
                },
                {
                    "attrs": {
                        # "disabled": None,
                        "id": "id_date_field_year",
                        # "placeholder": None,
                        "required": True,
                    },
                    "is_hidden": False,
                    "name": "date_field_year",
                    "optgroups": [
                        [
                            None,
                            [
                                {
                                    "label": "2000",
                                    "name": "date_field_year",
                                    "selected": False,
                                    "value": "2000",
                                }
                            ],
                            0.0,
                        ],
                        [
                            None,
                            [
                                {
                                    "label": "2001",
                                    "name": "date_field_year",
                                    "selected": False,
                                    "value": "2001",
                                }
                            ],
                            1.0,
                        ],
                    ],
                    "required": False,
                    "tag": "django.forms.widgets.Select",
                    "template_name": "django/forms/widgets/select.html",
                    "value": "2015",
                },
            ],
            "tag": "django.forms.widgets.SelectDateWidget",
            "template_name": "django/forms/widgets/select_date.html",
            "value": {"year": 2015, "month": 1, "day": 1},
        },
    }
    field_schema = create_schema(Form.base_fields["date_field"], schema.definitions)
    convert_to_json_and_validate(serialized["fields"]["date_field"], field_schema)

    assert serialized["fields"]["date_time_field"] == {
        "help_text": None,
        "label": "Date time field",
        "name": "date_time_field",
        "widget": {
            "attrs": {
                # "disabled": None,
                "id": "id_date_time_field",
                # "placeholder": None,
                "required": True,
            },
            "is_hidden": False,
            "name": "date_time_field",
            "required": True,
            "subwidgets": [
                {
                    "attrs": {
                        # "disabled": None,
                        # "format": None,
                        "id": "id_date_time_field_0",
                        # "placeholder": None,
                        "required": True,
                    },
                    "is_hidden": False,
                    "name": "date_time_field_0",
                    "required": False,
                    "tag": "django.forms.widgets.DateInput",
                    "template_name": "django/forms/widgets/date.html",
                    "type": "text",
                    "value": None,
                },
                {
                    "attrs": {
                        # "disabled": None,
                        # "format": None,
                        "id": "id_date_time_field_1",
                        # "placeholder": None,
                        "required": True,
                    },
                    "is_hidden": False,
                    "name": "date_time_field_1",
                    "required": False,
                    "tag": "django.forms.widgets.TimeInput",
                    "template_name": "django/forms/widgets/time.html",
                    "type": "text",
                    "value": None,
                },
            ],
            "tag": "django.forms.widgets.SplitDateTimeWidget",
            "template_name": "django/forms/widgets/splitdatetime.html",
            "value": None,
        },
    }
    field_schema = create_schema(
        Form.base_fields["date_time_field"], schema.definitions
    )
    convert_to_json_and_validate(serialized["fields"]["date_time_field"], field_schema)

    assert serialized["fields"]["boolean_field"] == {
        "name": "boolean_field",
        "label": "Boolean field",
        "help_text": "Not blank",
        "widget": {
            "template_name": "django/forms/widgets/checkbox.html",
            "name": "boolean_field",
            "is_hidden": False,
            "required": True,
            "value": True,
            "attrs": {
                "id": "id_boolean_field",
                # "disabled": None,
                "required": True,
                # "placeholder": None,
                "checked": True,
            },
            "type": "checkbox",
            "tag": "django.forms.widgets.CheckboxInput",
        },
    }
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
