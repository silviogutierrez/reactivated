import enum
from typing import Any, List, Literal, NamedTuple, Tuple, Type

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
    pick_nested: Pick[models.Composer, "name", Pick["operas", Opera]]
    pick_enum: Pick[models.Continent, "hemisphere"]
    fixed_tuple_different_types: Tuple[str, int]
    fixed_tuple_same_types: Tuple[str, str]
    complex_type_we_do_not_type: Any


def convert_to_json_and_validate(instance, schema):
    converted = simplejson.loads(simplejson.dumps(instance))
    validate(
        instance=converted, schema={"definitions": schema.definitions, **schema.schema}
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
        "pick_property": {"did_live_in_more_than_one_country": True,},
        "pick_literal": {"name": composer.name, "operas": [{"name": opera.name}]},
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
    assert serialized_form.fields["countries"].widget["optgroups"][0][1][0][
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
    assert "name" in serialized_form_set.forms[0].errors
    convert_to_json_and_validate(serialized_form_set, generated_schema)


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
