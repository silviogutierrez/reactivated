from __future__ import annotations

import dataclasses
import datetime
import enum
import json
import sys
import uuid
import warnings
from typing import Annotated, Any, Literal, TypedDict
from unittest.mock import Mock

import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser, User
from django.db import models as dj_models
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from reactivated import Pick
from reactivated.forms import FormField, form, get_form_schema
from reactivated.pick import export
from reactivated.router import Router
from reactivated.rpc.core import (
    PickAsDict,
    PickProxy,
    Primitive,
    _type_to_str,
    form_from_type_adapter,
    generate_server_schema,
    get_field_schema,
    manually_exported_registry,
    pick,
)
from reactivated.rpc.utils import flatten_schema


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


class PrincipalEchoForm(Pick):
    """Module-level so get_type_hints can resolve it."""

    value: str


class MyModel(BaseModel):
    snap: int


@form()
class RequiredTestForm(BaseModel):
    explicit_required: str = FormField(required=True)
    explicit_optional: str = FormField(required=False)
    inferred_required: str = FormField()
    inferred_optional: str | None = FormField()


@form()
class ReadOnlyTestForm(BaseModel):
    editable: str = FormField()
    read_only_field: str | None = FormField(read_only=True)
    optional_field: str | None = FormField(required=False)


@form()
class SelectWithEmptyOptionForm(BaseModel):
    unit: str = FormField(
        widget="select",
        required=False,
        options=(("", "Choose unit"), ("g", "g"), ("oz", "oz")),
    )
    category: str = FormField(
        widget="select",
        required=False,
        options=(("a", "Option A"), ("b", "Option B")),
    )


class _Stage(enum.Enum):
    LEAD = "Lead"
    SOLD = "Sold"


@form()
class OptionalSelectForm(BaseModel):
    status: Literal["NEW", "SOLD"] | None = FormField(widget="select", required=False)
    stage: _Stage | None = FormField(widget="select", required=False)


# Module-level picks for schema generation and .returns tests.
MyPick = pick(User, fields=["id"])
ReturnsPick = pick(User, fields=["id", "email"])
ListReturnsPick = pick(User, fields=["id", "email", "is_staff"])
NullableReturnsPick = pick(User, fields=["id", "email", "is_active"])
ExtraFieldsPick = pick(User, fields=["id", "email"], extra_fields={"score": int})


class Tag(TypedDict):
    name: str
    value: int


ComplexExtraFieldsPick = pick(
    User,
    fields=["id"],
    extra_fields={
        "tags": list[Tag],
        "label": str | None,
        "scores": list[tuple[str, int]],
    },
)


class OptionalFieldsModel(dj_models.Model):
    note = dj_models.CharField(max_length=100, null=True)
    scored = dj_models.IntegerField(null=True, default=0)

    class Meta:
        app_label = "rpc_optional_fields"


OptionalFieldsPick = pick(
    OptionalFieldsModel, fields=["id", "note"], optional_fields=["note"]
)


@pytest.fixture
def schema_env(tmp_path: Any, settings: Any) -> Any:
    """Set up a clean schema environment for pick tests."""
    sys.modules.pop("pick_schema", None)
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    settings.REACTIVATED_SERVER_SCHEMA = str(schema_dir)
    sys.path.insert(0, str(schema_dir))
    yield
    sys.path.remove(str(schema_dir))


def test_optional_fields(schema_env: Any) -> None:
    generate_server_schema(skip_cache=True)

    # Input: the key may be omitted and deserializes to None. Explicit values
    # and explicit nulls still validate as usual.
    validated = OptionalFieldsPick.input.model_validate({"id": 1})
    assert validated.note is None
    assert "note" not in validated.model_fields_set

    explicit = OptionalFieldsPick.input.model_validate({"id": 1, "note": "hi"})
    assert explicit.note == "hi"
    assert "note" in explicit.model_fields_set

    # Output is unaffected: server-side data always carries every picked
    # attribute, so "optional" is only meaningful for input payloads.
    with pytest.raises(ValidationError):
        OptionalFieldsPick.output.model_validate({"id": 1})
    assert (
        OptionalFieldsPick.output.model_validate({"id": 1, "note": None}).note is None
    )


def test_optional_fields_definition_guards() -> None:
    # Not nullable: absent-means-None requires None to be a legal value.
    with pytest.raises(AssertionError, match="nullable"):
        pick(User, fields=["id", "email"], optional_fields=["email"])

    # Model default: the implicit None would shadow it.
    with pytest.raises(AssertionError, match="default"):
        pick(
            OptionalFieldsModel,
            fields=["id", "scored"],
            optional_fields=["scored"],
        )


def test_generate_server_schema(settings: Any, tmp_path: Any) -> None:
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    schema_path = schema_dir / "pick_schema" / "__init__.py"

    settings.REACTIVATED_SERVER_SCHEMA = str(schema_dir)
    sys.path.insert(0, str(schema_dir))

    generate_server_schema()
    assert schema_path.exists()
    generated = schema_path.read_text()
    assert "MyPick" in generated

    sys.path.remove(str(schema_dir))


def test_schema_generation_with_rpc_and_picks(settings: Any, tmp_path: Any) -> None:
    class Another(BaseModel):
        thing: str

    MyType = TypeAdapter(int)
    WrappedAnother = TypeAdapter(Another)

    MyType.validate_python(5)
    MyType.validate_python("5", strict=False)
    WrappedAnother.validate_python({"thing": "blah"})

    router = Router(HttpRequest)

    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    schema_path = schema_dir / "pick_schema" / "__init__.py"

    settings.REACTIVATED_SERVER_SCHEMA = str(schema_dir)
    sys.path.insert(0, str(schema_dir))

    @router.rpc
    def rpc_call(request: HttpRequest, form: int | str | list[str]) -> None:
        pass

    @router.rpc
    def with_model(request: HttpRequest, form: MyModel) -> None:
        pass

    @router.rpc
    def with_pick(request: HttpRequest, form: MyPick.input) -> None:
        pass

    generate_server_schema()
    generated = schema_path.read_text()
    assert "MyPick" in generated


def test_enums() -> None:
    class MyEnum(enum.Enum):
        FOO = "Foo"
        BAR = "Bar"

    class WrongEnum(enum.Enum):
        SNAP = "Snap"

    class EnumTest(Pick):
        enum_test: MyEnum

    thing = EnumTest(enum_test=MyEnum.FOO)
    assert isinstance(thing.enum_test, MyEnum)
    assert isinstance(thing.model_dump()["enum_test"], MyEnum)
    assert thing.model_dump(mode="json")["enum_test"] == "FOO"
    EnumTest(enum_test="FOO")  # type: ignore[arg-type]
    EnumTest(enum_test=MyEnum.FOO)

    EnumTest.model_validate({"enum_test": "FOO"})
    EnumTest.model_validate({"enum_test": MyEnum.FOO})

    with pytest.raises(ValidationError):
        EnumTest.model_validate({"enum_test": "WRONG"})

    with pytest.raises(ValidationError):
        EnumTest.model_validate({"enum_test": WrongEnum.SNAP})


def test_enum_aliases() -> None:
    class EnumWithAliases(enum.Enum):
        V1 = False
        V2_A = False  # Alias for V1
        V2_B = True
        V2_C = True  # Alias for V2_B

    class AliasEnumTest(Pick):
        enum_test: EnumWithAliases

    AliasEnumTest.model_validate({"enum_test": "V1"})
    AliasEnumTest.model_validate({"enum_test": "V2_A"})
    AliasEnumTest.model_validate({"enum_test": "V2_B"})
    AliasEnumTest.model_validate({"enum_test": "V2_C"})

    instance_v2a = AliasEnumTest.model_validate({"enum_test": "V2_A"})
    assert instance_v2a.model_dump(mode="json")["enum_test"] == "V1"

    instance_v2c = AliasEnumTest.model_validate({"enum_test": "V2_C"})
    assert instance_v2c.model_dump(mode="json")["enum_test"] == "V2_B"

    schema = AliasEnumTest.model_json_schema()
    enum_values = schema["$defs"]["EnumWithAliases"]["enum"]
    assert "V1" in enum_values
    assert "V2_A" in enum_values
    assert "V2_B" in enum_values
    assert "V2_C" in enum_values


def test_enums_from_model_instance() -> None:
    class StatusEnum(enum.Enum):
        FOO = "Foo"
        BAR = "Bar"

    class EnumPick(Pick):
        enum_test: StatusEnum

    class EnumPickAsDict(PickAsDict):
        enum_test: StatusEnum

    class EnumPickAsDictContainer(BaseModel):
        child: EnumPickAsDict

    mock_model = Mock(spec=dj_models.Model)
    mock_model.enum_test = StatusEnum.FOO

    validated = EnumPick.model_validate(mock_model)
    assert validated.enum_test is StatusEnum.FOO
    assert validated.model_dump(mode="json")["enum_test"] == "FOO"

    mock_model_2 = Mock(spec=dj_models.Model)
    mock_model_2.enum_test = StatusEnum.BAR

    validated_model = EnumPickAsDictContainer.model_validate({"child": mock_model_2})
    assert validated_model.model_dump()["child"]["enum_test"] is StatusEnum.BAR


def test_app_enum_serializes_by_name_outside_pick_context() -> None:
    # The typed-refusal pattern: an RPC returns `MyEnum | SomePick`, so the
    # enum arm is schema-built with no Pick on the model stack. Ownership by
    # module origin decides: an enum defined in an installed Django app
    # speaks member NAMES on every wire with no export required.
    class Refusal(enum.Enum):
        NO_PHONE = "The contact has no phone number."

    Refusal.__module__ = "sample.server.apps.samples.models"

    class RefusalResult(Pick):
        outcome: str

    adapter: TypeAdapter[Any] = TypeAdapter(Refusal | RefusalResult)
    assert adapter.dump_python(Refusal.NO_PHONE, mode="json") == "NO_PHONE"
    assert adapter.validate_python("NO_PHONE") is Refusal.NO_PHONE

    # Non-app enums (third-party SDK models — this test module stands in)
    # keep pydantic's default value serialization.
    class ThirdParty(enum.Enum):
        A = "a-value"

    third: TypeAdapter[Any] = TypeAdapter(ThirdParty)
    assert third.dump_python(ThirdParty.A, mode="json") == "a-value"


def test_literal_app_enum_serializes_by_name_outside_pick_context() -> None:
    # Mirror of the bare-enum case for Literal[Enum.MEMBER]: an app-owned enum
    # inside a Literal (a union discriminant, or a narrowed bare return)
    # coerces and serializes by member NAME even with no Pick on the stack.
    class Outcome(enum.Enum):
        WON = "won-value"
        LOST = "lost-value"

    Outcome.__module__ = "sample.server.apps.samples.models"

    adapter: TypeAdapter[Any] = TypeAdapter(Literal[Outcome.WON, Outcome.LOST])
    assert adapter.dump_python(Outcome.WON, mode="json") == "WON"
    assert adapter.validate_python("WON") is Outcome.WON

    # A pure string Literal has no enum members to coerce — left untouched.
    plain: TypeAdapter[Any] = TypeAdapter(Literal["a", "b"])
    assert plain.dump_python("a", mode="json") == "a"


def test_auto_export_names_direct_rpc_types() -> None:
    from reactivated.rpc.core import _auto_export_name

    app_module = "sample.server.apps.samples.models"

    class WidgetResult(Pick):
        status: str

    WidgetResult.__module__ = app_module

    # A Pick used directly as an RPC input/output names itself by qualname.
    name = _auto_export_name(WidgetResult, app_module)
    assert name is not None and name.endswith(".WidgetResult")

    # A bare, unnamed Literal has no module-level binding — it stays inline and
    # is named via the RPC's own output slot (P3) instead.
    assert _auto_export_name(Literal["a", "b"], app_module) is None

    # Enums are excluded (no input/output attrs); they keep explicit export()
    # for the runtime value map.
    class Flavor(enum.Enum):
        SWEET = "sweet"

    Flavor.__module__ = app_module
    assert _auto_export_name(Flavor, app_module) is None


def test_enums_pick_as_dict_by_name() -> None:
    class Status(enum.Enum):
        ACTIVE = "Active"

    class StatusDict(PickAsDict):
        status: Status

    class Container(BaseModel):
        child: StatusDict

    validated = Container.model_validate({"child": {"status": "ACTIVE"}})
    assert validated.model_dump(mode="json")["child"]["status"] == "ACTIVE"


def test_model_validate() -> None:
    user = User(email="testing@testing.com", username="testing")

    class Child(PickAsDict):
        email: str

    class Parent(PickAsDict):
        children: list[Child]

    class Container(BaseModel):
        parent: Parent

    validated = Container.model_validate(
        {"parent": {"children": [user]}},
    )

    assert (
        validated.model_dump()["parent"]["children"][0]["email"]
        == "testing@testing.com"
    )


def test_primitive_serialization() -> None:
    adapter: TypeAdapter[Any] = TypeAdapter(Primitive[str] | Literal["ONE", "TWO"])
    primitive_instance = Primitive(value="blah")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = adapter.dump_python(primitive_instance, mode="json")

    assert result == {"value": "blah"}


def test_form_generation() -> None:
    class MyForm(Pick):
        char_field: str | None
        boolean_field: bool | None

    form_from_type_adapter(TypeAdapter(MyForm))


def test_export_class_literal_and_union() -> None:
    initial_count = len(manually_exported_registry)

    @export(name="rpc.tests.ExportedClass")
    class ExportedClass(Pick):
        name: str

    assert "rpc.tests.ExportedClass" in manually_exported_registry

    ExportedLiteral = Literal["a", "b", "c"]
    export(name="rpc.tests.ExportedLiteral")(ExportedLiteral)
    assert "rpc.tests.ExportedLiteral" in manually_exported_registry

    class TypeA(TypedDict):
        type: Literal["a"]
        value_a: str

    class TypeB(TypedDict):
        type: Literal["b"]
        value_b: int

    ExportedUnion = TypeA | TypeB
    export(name="rpc.tests.ExportedUnion")(ExportedUnion)
    assert "rpc.tests.ExportedUnion" in manually_exported_registry

    assert len(manually_exported_registry) == initial_count + 3


def test_select_with_empty_option_schema() -> None:
    schema = get_form_schema(SelectWithEmptyOptionForm)

    assert schema["fields"]["unit"]["required"] is True
    assert schema["defaults"]["unit"] == ""

    assert "required" not in schema["fields"]["category"]
    assert schema["defaults"]["category"] is None


def test_datetime_fields_get_a_datetime_widget() -> None:
    # datetime.datetime must not degrade to the date-only widget: the time
    # component would be silently dropped at input.
    @form()
    class ScheduleForm(BaseModel):
        starts_on: datetime.date = FormField()
        starts_at: datetime.datetime = FormField()

    schema = get_form_schema(ScheduleForm)

    assert schema["fields"]["starts_on"]["type"] == "date"
    assert schema["fields"]["starts_at"]["type"] == "datetime"


def test_optional_select_extracts_options() -> None:
    # Optional select fields must extract options from the non-None union
    # member, whether the union is a UnionType instance (`SomeEnum | None`)
    # or a typing.Union generic (`Literal[...] | None`).
    schema = get_form_schema(OptionalSelectForm)

    assert schema["fields"]["status"]["options"] == [
        ("NEW", "NEW"),
        ("SOLD", "SOLD"),
    ]
    assert schema["fields"]["stage"]["options"] == [
        ("LEAD", "Lead"),
        ("SOLD", "Sold"),
    ]


@pytest.mark.asyncio
async def test_get_method_handling(settings: Any, rf: Any) -> None:
    settings.DEBUG = False
    router = Router(HttpRequest)

    # No form param — tests pure HTTP method handling.
    # (int/str are DJANGO_CONVERTERS so they become URL path params, not body forms.)
    @router.rpc(atomic_requests=False)
    def post_only(request: HttpRequest) -> None:
        pass

    @router.rpc(methods=["GET", "POST"], atomic_requests=False)
    def get_allowed(request: HttpRequest) -> None:
        pass

    request = rf.get(f"/{router.handlers['rpc_post_only']['url']}")
    request.user = AnonymousUser()
    response = await router.handlers["rpc_post_only"]["handler"](request)
    assert response.status_code == 405

    request = rf.get(f"/{router.handlers['rpc_get_allowed']['url']}")
    request.user = AnonymousUser()
    response = await router.handlers["rpc_get_allowed"]["handler"](request)
    assert response.status_code == 200

    request = rf.post(
        f"/{router.handlers['rpc_post_only']['url']}",
        data="null",
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_post_only"]["handler"](request)
    assert response.status_code == 200

    # A None-typed body param is forbidden at registration; a no-body RPC is
    # declared by omitting the param entirely (as post_only above does).
    with pytest.raises(TypeError, match="None-typed param"):

        @router.rpc(atomic_requests=False)
        def none_body(request: HttpRequest, form: None) -> None:
            pass


@pytest.mark.asyncio
async def test_router_authentication(settings: Any, rf: Any) -> None:
    settings.DEBUG = False

    router = Router(HttpRequest)

    @router.scope
    def authentication(request: HttpRequest) -> "HttpRequest | Literal[False]":
        if isinstance(request.user, AnonymousUser):
            return False
        return request

    @authentication.rpc(atomic_requests=False)
    def guarded(request: HttpRequest) -> str:
        return request.user.username

    @authentication.rpc(atomic_requests=False)
    async def async_guarded(request: HttpRequest) -> str:
        return request.user.username

    @router.rpc(atomic_requests=False)
    def open_to_all(request: HttpRequest) -> str:
        return "anyone"

    def make_request(name: str) -> Any:
        return rf.post(
            f"/{router.handlers[name]['url']}",
            data="null",
            content_type="application/json",
        )

    request = make_request("rpc_guarded")
    request.user = AnonymousUser()
    response = await router.handlers["rpc_guarded"]["handler"](request)
    assert response.status_code == 401
    assert json.loads(response.content) == {"error": "UNAUTHORIZED"}

    request = make_request("rpc_guarded")
    request.user = User(username="boss")
    response = await router.handlers["rpc_guarded"]["handler"](request)
    assert response.status_code == 200
    assert json.loads(response.content) == "boss"

    request = make_request("rpc_async_guarded")
    request.user = AnonymousUser()
    response = await router.handlers["rpc_async_guarded"]["handler"](request)
    assert response.status_code == 401
    assert json.loads(response.content) == {"error": "UNAUTHORIZED"}

    request = make_request("rpc_async_guarded")
    request.user = User(username="boss")
    response = await router.handlers["rpc_async_guarded"]["handler"](request)
    assert response.status_code == 200
    assert json.loads(response.content) == "boss"

    request = make_request("rpc_open_to_all")
    request.user = AnonymousUser()
    response = await router.handlers["rpc_open_to_all"]["handler"](request)
    assert response.status_code == 200
    assert json.loads(response.content) == "anyone"


@pytest.mark.asyncio
async def test_form_required_validation(rf: Any) -> None:
    router = Router(HttpRequest)

    @router.rpc(atomic_requests=False)
    def required_test(request: Any, form: RequiredTestForm) -> str:
        return "ok"

    # All filled -> 200
    request = rf.post(
        f"/{router.handlers['rpc_required_test']['url']}",
        data=json.dumps(
            {
                "explicit_required": "value",
                "explicit_optional": "value",
                "inferred_required": "value",
                "inferred_optional": "value",
            }
        ),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 200

    # Empty explicit_required -> 400
    request = rf.post(
        f"/{router.handlers['rpc_required_test']['url']}",
        data=json.dumps(
            {
                "explicit_required": "",
                "explicit_optional": "",
                "inferred_required": "value",
                "inferred_optional": None,
            }
        ),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 400
    errors = json.loads(response.content)
    assert any(e["loc"] == ["explicit_required"] for e in errors)

    # Empty explicit_optional + filled required fields -> 200
    request = rf.post(
        f"/{router.handlers['rpc_required_test']['url']}",
        data=json.dumps(
            {
                "explicit_required": "value",
                "explicit_optional": "",
                "inferred_required": "value",
                "inferred_optional": None,
            }
        ),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 200

    # Empty inferred_required -> 400
    request = rf.post(
        f"/{router.handlers['rpc_required_test']['url']}",
        data=json.dumps(
            {
                "explicit_required": "value",
                "explicit_optional": "",
                "inferred_required": "",
                "inferred_optional": None,
            }
        ),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 400
    errors = json.loads(response.content)
    assert any(e["loc"] == ["inferred_required"] for e in errors)

    # None for inferred_optional + filled required fields -> 200
    request = rf.post(
        f"/{router.handlers['rpc_required_test']['url']}",
        data=json.dumps(
            {
                "explicit_required": "value",
                "explicit_optional": "value",
                "inferred_required": "value",
                "inferred_optional": None,
            }
        ),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 200

    # Read-only fields are set to None regardless of client input
    @router.rpc(atomic_requests=False)
    def read_only_test(request: Any, form: ReadOnlyTestForm) -> str:
        assert form.editable == "value"
        assert form.read_only_field is None
        assert form.optional_field is None
        return "ok"

    request = rf.post(
        f"/{router.handlers['rpc_read_only_test']['url']}",
        data=json.dumps({"editable": "value"}),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_read_only_test"]["handler"](request)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_sync_rpc_rolls_back_on_errors(rf: Any) -> None:
    router = Router(HttpRequest)

    # Use list[str] because bare str is a DJANGO_CONVERTER (URL path param).
    @router.rpc
    def sync_expected(request: HttpRequest, form: list[str]) -> None:
        User.objects.create(username=form[0], email=form[0])
        raise AssertionError("Expected")

    @router.rpc
    def sync_unexpected(request: HttpRequest, form: list[str]) -> None:
        User.objects.create(username=form[0], email=form[0])
        1 / 0

    generate_server_schema()

    expected_email = unique_email()
    request = rf.post(
        f"/{router.handlers['rpc_sync_expected']['url']}",
        data=json.dumps([expected_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()

    response = await router.handlers["rpc_sync_expected"]["handler"](request)
    assert response.status_code == 400
    assert not await sync_to_async(User.objects.filter(email=expected_email).exists)()

    unexpected_email = unique_email()
    request = rf.post(
        f"/{router.handlers['rpc_sync_unexpected']['url']}",
        data=json.dumps([unexpected_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    with pytest.raises(ZeroDivisionError):
        await router.handlers["rpc_sync_unexpected"]["handler"](request)
    assert not await sync_to_async(User.objects.filter(email=unexpected_email).exists)()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_async_rpc_atomicity(rf: Any) -> None:
    # An async handler now honors atomic_requests: under atomic (the default)
    # its writes roll back on error like a sync handler's, because the chain is
    # bounced onto a sync transaction thread; with atomic_requests=False it runs
    # loose and its writes persist.
    router = Router(HttpRequest)

    @router.rpc
    async def atomic_rpc(request: HttpRequest, form: list[str]) -> None:
        await sync_to_async(User.objects.create)(username=form[0], email=form[0])
        raise AssertionError("Expected")

    @router.rpc(atomic_requests=False)
    async def loose_rpc(request: HttpRequest, form: list[str]) -> None:
        await sync_to_async(User.objects.create)(username=form[0], email=form[0])
        raise AssertionError("Expected")

    atomic_email = unique_email()
    request = rf.post(
        f"/{router.handlers['rpc_atomic_rpc']['url']}",
        data=json.dumps([atomic_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_atomic_rpc"]["handler"](request)
    assert response.status_code == 400
    # rolled back
    assert not await sync_to_async(User.objects.filter(email=atomic_email).exists)()

    loose_email = unique_email()
    request = rf.post(
        f"/{router.handlers['rpc_loose_rpc']['url']}",
        data=json.dumps([loose_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_loose_rpc"]["handler"](request)
    assert response.status_code == 400
    # persisted (no transaction)
    assert await sync_to_async(User.objects.filter(email=loose_email).exists)()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_single_model(rf: Any, schema_env: Any) -> None:
    router = Router(HttpRequest)

    @router.rpc
    def get_user_returns(request: Any, form: list[int]) -> ReturnsPick.returns:
        return User.objects.get(id=form[0])

    generate_server_schema(skip_cache=True)

    email = unique_email()
    user = await sync_to_async(User.objects.create)(username=email, email=email)

    request = rf.post(
        f"/{router.handlers['rpc_get_user_returns']['url']}",
        data=json.dumps([user.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_get_user_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == user.id
    assert data["email"] == email


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_list_of_models(rf: Any, schema_env: Any) -> None:
    router = Router(HttpRequest)

    email1 = unique_email()
    email2 = unique_email()

    @router.rpc
    def list_users_returns(
        request: Any, form: list[int]
    ) -> list[ListReturnsPick.returns]:
        return list(User.objects.filter(id__in=form))

    generate_server_schema(skip_cache=True)

    user1 = await sync_to_async(User.objects.create)(username=email1, email=email1)
    user2 = await sync_to_async(User.objects.create)(username=email2, email=email2)

    request = rf.post(
        f"/{router.handlers['rpc_list_users_returns']['url']}",
        data=json.dumps([user1.id, user2.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_list_users_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    emails = {item["email"] for item in data}
    assert email1 in emails
    assert email2 in emails


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_nullable(rf: Any, schema_env: Any) -> None:
    router = Router(HttpRequest)

    @router.rpc
    def maybe_user_returns(
        request: Any, form: list[int]
    ) -> NullableReturnsPick.returns | None:
        return User.objects.filter(id=form[0]).first()

    generate_server_schema(skip_cache=True)

    request = rf.post(
        f"/{router.handlers['rpc_maybe_user_returns']['url']}",
        data=json.dumps([99999]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_maybe_user_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data is None

    email = unique_email()
    user = await sync_to_async(User.objects.create)(username=email, email=email)
    request = rf.post(
        f"/{router.handlers['rpc_maybe_user_returns']['url']}",
        data=json.dumps([user.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_maybe_user_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == user.id
    assert data["email"] == email


def test_get_field_schema_unions_and_annotated() -> None:
    """get_field_schema handles multi-type unions and Annotated wrappers."""

    class TypeA(TypedDict):
        type: Literal["a"]
        value: str

    class TypeB(TypedDict):
        type: Literal["b"]
        count: int

    # Multi-type union
    union_type = TypeA | TypeB
    result = get_field_schema(union_type, mode="output")
    assert result["type"] == "field"
    assert "TypeA" in result["field_class"]
    assert "TypeB" in result["field_class"]
    assert result["nullable"] is False

    # X | None still works
    nullable_result = get_field_schema(str | None, mode="output")
    assert nullable_result["nullable"] is True

    # Annotated wrappers are stripped
    annotated = Annotated[TypeA | TypeB, Field(discriminator="type")]
    annotated_result = get_field_schema(annotated, mode="output")
    assert annotated_result["type"] == "field"
    assert "TypeA" in annotated_result["field_class"]
    assert "TypeB" in annotated_result["field_class"]

    # list[Annotated[A | B, ...]] — the real-world Lead.interactions case
    list_type = list[Annotated[TypeA | TypeB, Field(discriminator="type")]]
    list_result = get_field_schema(list_type, mode="output")
    assert list_result["type"] == "list"
    assert list_result["items"]["type"] == "field"
    assert "TypeA" in list_result["items"]["field_class"]
    assert "TypeB" in list_result["items"]["field_class"]

    # A union with a typing-construct member is typing.Union (a
    # _GenericAlias), not types.UnionType — it must take the union branch,
    # not the generic-alias repr() fallback, which emits an unimportable
    # `typing.Optional[...]` annotation.
    optional_annotated = Annotated[TypeA | TypeB, Field(discriminator="type")] | None
    optional_result = get_field_schema(optional_annotated, mode="output")
    assert optional_result["type"] == "field"
    assert optional_result["nullable"] is True
    assert "typing." not in optional_result["field_class"]
    assert "TypeA" in optional_result["field_class"]
    assert "TypeB" in optional_result["field_class"]


def test_literal_enum_in_discriminated_union() -> None:
    """Literal[EnumMember] in a discriminated union validates from dicts/JSON strings."""

    class ActionKind(enum.Enum):
        SEND_EMAIL = "SEND_EMAIL"
        CALL = "CALL"

    class SendEmail(Pick):
        action: Literal[ActionKind.SEND_EMAIL]
        subject: str

    class Call(Pick):
        action: Literal[ActionKind.CALL]

    class Suggestion(Pick):
        suggestion: SendEmail | Call

    # From dict with string values (simulates JSON deserialization)
    result = Suggestion.model_validate(
        {"suggestion": {"action": "SEND_EMAIL", "subject": "Hi"}}
    )
    assert result.suggestion.action == ActionKind.SEND_EMAIL
    assert isinstance(result.suggestion, SendEmail)

    result2 = Suggestion.model_validate({"suggestion": {"action": "CALL"}})
    assert result2.suggestion.action == ActionKind.CALL
    assert isinstance(result2.suggestion, Call)

    # From JSON string (the actual failing case from Anthropic messages.parse)
    result3 = Suggestion.model_validate_json(
        '{"suggestion": {"action": "SEND_EMAIL", "subject": "Hello"}}'
    )
    assert result3.suggestion.action == ActionKind.SEND_EMAIL

    result4 = Suggestion.model_validate_json('{"suggestion": {"action": "CALL"}}')
    assert isinstance(result4.suggestion, Call)

    # Direct Literal[EnumMember] field on a Pick
    class DirectLiteral(Pick):
        action: Literal[ActionKind.SEND_EMAIL]

    validated = DirectLiteral.model_validate({"action": "SEND_EMAIL"})
    assert validated.action == ActionKind.SEND_EMAIL

    # Wrong value still fails
    with pytest.raises(ValidationError):
        Suggestion.model_validate(
            {"suggestion": {"action": "INVALID", "subject": "Hi"}}
        )


def test_literal_enum_as_union_discriminator() -> None:
    """Literal[Enum.MEMBER] works as an EXPLICIT Field(discriminator=...) tag.

    Pydantic reads a tagged union's tag values statically out of the
    discriminator field's core schema and refuses function-wrap validators
    there — which the by-name enum coercion used to be. It is now an
    after-validator over a names+members literal, which pydantic can see
    through, so app enums can discriminate unions directly."""

    class Kind(enum.Enum):
        TIMED = "Timed"
        ALL_DAY = "All Day"

    class Timed(Pick):
        kind: Literal[Kind.TIMED]
        hour: int

    class AllDay(Pick):
        kind: Literal[Kind.ALL_DAY]
        day: str

    class Holder(Pick):
        slot: Annotated[Timed | AllDay, Field(discriminator="kind")]

    # Wire NAMES pick the arm, as do Python members and direct construction.
    holder = Holder.model_validate({"slot": {"kind": "ALL_DAY", "day": "2026-08-04"}})
    assert isinstance(holder.slot, AllDay)
    assert holder.slot.kind is Kind.ALL_DAY
    assert isinstance(
        Holder.model_validate({"slot": {"kind": Kind.TIMED, "hour": 9}}).slot, Timed
    )
    Holder(slot=Timed(kind=Kind.TIMED, hour=9))

    with pytest.raises(ValidationError):
        Holder.model_validate({"slot": {"kind": "NOPE", "day": ""}})

    # The wire and the arm field schemas — what generated TypeScript is built
    # from (the generator reads oneOf + arm properties) — speak NAMES only.
    assert holder.model_dump(mode="json")["slot"]["kind"] == "ALL_DAY"
    schema = Holder.model_json_schema()
    arm_kind = json.dumps(schema["$defs"]["AllDay"]["properties"]["kind"])
    assert "ALL_DAY" in arm_kind
    assert "All Day" not in arm_kind
    # The openapi discriminator.mapping keys BOTH spellings to the same arm
    # (runtime accepts both) — metadata the TS generator never reads.
    mapping = schema["properties"]["slot"]["discriminator"]["mapping"]
    assert mapping["ALL_DAY"] == mapping["All Day"]


def test_literal_enum_name_value_mismatch() -> None:
    """Literal[Enum.MEMBER] speaks member NAMES on the wire even when the
    member's value differs — validation, dump, and JSON schema agree."""

    class Version(enum.Enum):
        V1 = "v1"

    class Task(Pick):
        version: Literal[Version.V1]

    task = Task.model_validate({"version": "V1"})
    assert task.version is Version.V1
    # Passing the member itself still validates.
    assert Task.model_validate({"version": Version.V1}).version is Version.V1

    dumped = task.model_dump(mode="json")
    assert dumped == {"version": "V1"}
    assert Task.model_validate(dumped).version is Version.V1

    # The JSON schema (and thus generated TypeScript) advertises the name.
    schema = Task.model_json_schema()["properties"]["version"]
    assert "v1" not in json.dumps(schema)
    assert "V1" in json.dumps(schema)

    with pytest.raises(ValidationError):
        Task.model_validate({"version": "v1"})


def test_pick_proxy_basic() -> None:
    """PickProxy delegates model attrs and exposes extras."""
    mock_model = Mock(spec=dj_models.Model)
    mock_model.id = 42
    mock_model.email = "test@example.com"

    proxy = PickProxy(mock_model, score=99, label="high")

    # Extras are found directly
    assert proxy.score == 99
    assert proxy.label == "high"

    # Model attrs are delegated
    assert proxy.id == 42
    assert proxy.email == "test@example.com"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_with_extra_fields(rf: Any, schema_env: Any) -> None:
    """RPC handler returns PickProxy, response includes both model fields and extras."""
    router = Router(HttpRequest)

    @router.rpc
    def get_user_with_score(request: Any, form: list[int]) -> ExtraFieldsPick.returns:
        user = User.objects.get(id=form[0])
        return PickProxy(user, score=42)

    generate_server_schema(skip_cache=True)

    email = unique_email()
    user = await sync_to_async(User.objects.create)(username=email, email=email)

    request = rf.post(
        f"/{router.handlers['rpc_get_user_with_score']['url']}",
        data=json.dumps([user.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_get_user_with_score"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == user.id
    assert data["email"] == email
    assert data["score"] == 42


def test_schema_generation_with_extra_fields(settings: Any, tmp_path: Any) -> None:
    """Generated schema contains extras TypedDict, proxy method, PickProxy-based returns."""
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    schema_path = schema_dir / "pick_schema" / "__init__.py"

    settings.REACTIVATED_SERVER_SCHEMA = str(schema_dir)
    sys.path.insert(0, str(schema_dir))

    generate_server_schema()
    assert schema_path.exists()
    generated = schema_path.read_text()

    # Extras TypedDict should be generated
    assert "ExtraFieldsPick_extras" in generated
    assert "TypedDict" in generated

    # proxy method should be generated
    assert "def proxy" in generated
    assert "PickProxy" in generated
    assert "Unpack" in generated

    # returns should use PickProxy, not model ref
    assert "Annotated[PickProxy, ReturnsMarker[" in generated

    # Complex extra_fields types should be properly serialized
    assert "ComplexExtraFieldsPick_extras" in generated
    assert "builtins.list[tests.rpc.Tag]" in generated
    assert "builtins.str | None" in generated
    assert "builtins.list[builtins.tuple[builtins.str, builtins.int]]" in generated

    sys.path.remove(str(schema_dir))


class _Color(enum.StrEnum):
    RED = "RED"
    GREEN = "GREEN"


class _FlattenTarget(Pick):
    action: Literal["CREATE"]
    color: _Color
    items: list[Pick]


def test_flatten_schema() -> None:
    schema = _FlattenTarget.model_json_schema()
    assert "$defs" in schema

    result = flatten_schema(schema)
    serialized = json.dumps(result)

    assert "$defs" not in result
    assert "$ref" not in serialized
    assert '"title"' not in serialized
    assert '"format"' not in serialized
    assert result["properties"]["action"]["const"] == "CREATE"
    assert result["properties"]["color"]["enum"] == ["RED", "GREEN"]


def test_type_to_str_pick_holder() -> None:
    assert _type_to_str(MyPick) == f"{MyPick.get_name()}_output"  # type: ignore[attr-defined]


class ObserverInput(BaseModel):
    value: int


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc,expected_status",
    [
        (Exception("boom"), "ERROR"),
        (None, "SUCCESS"),
    ],
)
async def test_observer_notified(
    rf: Any, schema_env: Any, exc: Exception | None, expected_status: str
) -> None:
    from reactivated.rpc.observer import RequestStatus, rpc_observer

    calls: list[tuple[RequestStatus, BaseException | None]] = []

    @rpc_observer
    async def observer(
        request: Any,
        rpc_name: str,
        log: Any,
        status: RequestStatus,
        input: Any,
        output: Any,
        body: Any,
        exception: BaseException | None,
    ) -> None:
        calls.append((status, exception))

    router = Router(HttpRequest)

    # atomic_requests=False: this handler touches no DB, and an async handler
    # now opens a transaction under atomic (which would demand the db fixture).
    @router.rpc(log=True, atomic_requests=False)
    async def observed(request: HttpRequest, form: ObserverInput) -> int:
        if exc:
            raise exc
        return form.value

    generate_server_schema(skip_cache=True)

    request = rf.post(
        f"/{router.handlers['rpc_observed']['url']}",
        data={"value": 1},
        content_type="application/json",
    )
    request.user = AnonymousUser()

    if exc:
        with pytest.raises(type(exc)):
            await router.handlers["rpc_observed"]["handler"](request)
    else:
        response = await router.handlers["rpc_observed"]["handler"](request)
        assert response.status_code == 200

    assert len(calls) == 1
    assert calls[0][0] == RequestStatus[expected_status]


@pytest.mark.asyncio
async def test_router_principal_injection(settings: Any, rf: Any) -> None:
    """A scope resolves the principal — any value — and the handler receives
    it as its first (positionally excluded) parameter. Parameters typed
    HttpRequest beyond the principal slot are injected."""
    settings.DEBUG = False

    router = Router()  # request_type defaults to HttpRequest

    @router.scope
    def authenticated(request: HttpRequest) -> "User | Literal[False]":
        if isinstance(request.user, AnonymousUser):
            return False
        assert isinstance(request.user, User)
        return request.user

    @authenticated.rpc(atomic_requests=False)
    def whoami(user: User) -> str:
        return user.username

    @authenticated.rpc(atomic_requests=False)
    def with_request(user: User, request: HttpRequest) -> str:
        return f"{user.username}:{request.method}"

    @authenticated.rpc(atomic_requests=False)
    def with_request_and_form(
        user: User, request: HttpRequest, form: PrincipalEchoForm
    ) -> str:
        return f"{user.username}:{request.method}:{form.value}"

    def make_request(name: str) -> Any:
        return rf.post(
            f"/{router.handlers[name]['url']}",
            data="null",
            content_type="application/json",
        )

    request = make_request("rpc_whoami")
    request.user = AnonymousUser()
    response = await router.handlers["rpc_whoami"]["handler"](request)
    assert response.status_code == 401

    request = make_request("rpc_whoami")
    request.user = User(username="boss")
    response = await router.handlers["rpc_whoami"]["handler"](request)
    assert response.status_code == 200
    assert json.loads(response.content) == "boss"

    request = make_request("rpc_with_request")
    request.user = User(username="boss")
    response = await router.handlers["rpc_with_request"]["handler"](request)
    assert response.status_code == 200
    assert json.loads(response.content) == "boss:POST"

    request = rf.post(
        f"/{router.handlers['rpc_with_request_and_form']['url']}",
        data=json.dumps({"value": "hi"}),
        content_type="application/json",
    )
    request.user = User(username="boss")
    response = await router.handlers["rpc_with_request_and_form"]["handler"](request)
    assert response.status_code == 200
    assert json.loads(response.content) == "boss:POST:hi"


@dataclasses.dataclass
class Box:
    pk: int


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_rpc_accepts_scopes(rf: Any) -> None:
    """@router.rpc(scope): the chain runs like a view's — products injected,
    scope URL params join the rpc URL — and EVERY failure (False or an
    HttpResponse) coerces to the uniform denial. JSON callers never see a
    redirect."""
    router = Router()

    @router.scope
    def gate(request: HttpRequest) -> "Box | HttpResponse | Literal[False]":
        if request.META.get("HTTP_X_DENY"):
            return False
        if request.META.get("HTTP_X_REDIRECT"):
            return HttpResponseRedirect("/login/")
        return Box(pk=0)

    @gate.scope
    def item(box: Box, *, item_id: int) -> "Box | HttpResponse":
        return Box(pk=item_id)

    @router.rpc(item)
    def double_item(box: Box, form: list[str]) -> int:
        return box.pk * 2

    # The scope's URL param joins the rpc URL (and therefore the TS args).
    assert router.handlers["rpc_double_item"]["url"] == "rpc/double_item/<int:item_id>/"
    assert ("rpc/double_item/<int:item_id>/", "rpc_double_item") in router.routes()

    handler = router.handlers["rpc_double_item"]["handler"]

    ok = rf.post(
        "/rpc/double_item/21/", data=json.dumps([]), content_type="application/json"
    )
    ok.user = AnonymousUser()
    response = await handler(ok, item_id=21)
    assert response.status_code == 200
    assert json.loads(response.content) == 42

    denied = rf.post(
        "/rpc/double_item/21/", data=json.dumps([]), content_type="application/json"
    )
    denied.user = AnonymousUser()
    denied.META["HTTP_X_DENY"] = "1"
    response = await handler(denied, item_id=21)
    assert response.status_code == 401

    # A page-flavored failure — a redirect — coerces to the same denial.
    redirected = rf.post(
        "/rpc/double_item/21/", data=json.dumps([]), content_type="application/json"
    )
    redirected.user = AnonymousUser()
    redirected.META["HTTP_X_REDIRECT"] = "1"
    response = await handler(redirected, item_id=21)
    assert response.status_code == 401
    assert json.loads(response.content) == {"error": "UNAUTHORIZED"}


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_atomic_requests_spans_the_scope_chain(rf: Any) -> None:
    """The request transaction opens before the scope chain runs — a scope
    may select_for_update a row the handler then mutates, so both must share
    it. Error paths must leave the shared sync thread with no dangling
    transaction, or the next request on that thread inherits it."""
    router = Router()
    seen: dict[str, bool] = {}

    @router.scope
    def gate(request: HttpRequest) -> Box:
        seen["scope"] = transaction.get_connection().in_atomic_block
        return Box(pk=1)

    @router.rpc(gate)
    def atomic_probe(box: Box, form: list[str]) -> bool:
        return bool(transaction.get_connection().in_atomic_block)

    @router.rpc(gate, atomic_requests=False)
    def bare_probe(box: Box, form: list[str]) -> bool:
        return bool(transaction.get_connection().in_atomic_block)

    @router.rpc(gate)
    def exploding(box: Box, form: list[str]) -> bool:
        raise RuntimeError("boom")

    def make_request() -> Any:
        request = rf.post(
            "/rpc/probe/", data=json.dumps([]), content_type="application/json"
        )
        request.user = AnonymousUser()
        return request

    async def thread_in_atomic_block() -> bool:
        return await sync_to_async(
            lambda: bool(transaction.get_connection().in_atomic_block)
        )()

    response = await router.handlers["rpc_atomic_probe"]["handler"](make_request())
    assert json.loads(response.content) is True
    assert seen["scope"] is True
    assert await thread_in_atomic_block() is False

    seen.clear()
    response = await router.handlers["rpc_bare_probe"]["handler"](make_request())
    assert json.loads(response.content) is False
    assert seen["scope"] is False

    with pytest.raises(RuntimeError, match="boom"):
        await router.handlers["rpc_exploding"]["handler"](make_request())
    assert await thread_in_atomic_block() is False


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_scope_writes_survive_an_assertion_rejection(rf: Any) -> None:
    """An AssertionError coerces to a 400 that rolls back only the handler
    savepoint — writes made by the scope chain (e.g. instantiate-on-read)
    must commit with the request."""
    router = Router()

    @router.scope
    def recorder(request: HttpRequest) -> User:
        return User.objects.create(username="scope-made")

    @router.rpc(recorder)
    def rejecting(user: User, form: list[str]) -> bool:
        User.objects.create(username="handler-made")
        raise AssertionError("nope")

    request = rf.post(
        "/rpc/rejecting/", data=json.dumps([]), content_type="application/json"
    )
    request.user = AnonymousUser()
    response = await router.handlers["rpc_rejecting"]["handler"](request)

    assert response.status_code == 400
    assert json.loads(response.content) == ["nope"]
    assert await sync_to_async(User.objects.filter(username="scope-made").exists)()
    assert not await sync_to_async(
        User.objects.filter(username="handler-made").exists
    )()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_failing_observer_cannot_roll_back_a_reported_success(rf: Any) -> None:
    """Observers run only after the request transaction closes. A failing
    observer write inside the still-open transaction would mark it for
    rollback: the handler's success would silently vanish while the client
    was told 200."""
    from reactivated.rpc import observer as observer_module
    from reactivated.rpc.observer import rpc_observer

    router = Router()
    observed_in_atomic: list[bool] = []

    @router.rpc()
    def register(request: HttpRequest, form: list[str]) -> str:
        return User.objects.create(username="registered").username

    previous = observer_module._observer

    @rpc_observer
    async def failing_observer(*args: Any) -> None:
        def failing_write() -> None:
            observed_in_atomic.append(transaction.get_connection().in_atomic_block)
            User.objects.create(username="registered")

        await sync_to_async(failing_write)()

    try:
        request = rf.post(
            "/rpc/register/", data=json.dumps([]), content_type="application/json"
        )
        request.user = AnonymousUser()
        response = await router.handlers["rpc_register"]["handler"](request)
    finally:
        observer_module._observer = previous

    assert response.status_code == 200
    assert json.loads(response.content) == "registered"
    assert observed_in_atomic == [False]
    assert await sync_to_async(User.objects.filter(username="registered").exists)()
