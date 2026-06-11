from __future__ import annotations

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
from django.http import HttpRequest
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from reactivated.rpc import FormField, Pick, Router, export, form
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
from reactivated.rpc.forms import get_form_schema
from reactivated.rpc.utils import flatten_schema


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


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

    rpc = Router()

    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    schema_path = schema_dir / "pick_schema" / "__init__.py"

    settings.REACTIVATED_SERVER_SCHEMA = str(schema_dir)
    sys.path.insert(0, str(schema_dir))

    @rpc()
    def rpc_call(request: HttpRequest, form: int | str | list[str]) -> None:
        pass

    @rpc()
    def with_model(request: HttpRequest, form: MyModel) -> None:
        pass

    @rpc()
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


@pytest.mark.asyncio
async def test_get_method_handling(settings: Any, rf: Any) -> None:
    settings.DEBUG = False
    rpc = Router()

    # No form param — tests pure HTTP method handling.
    # (int/str are DJANGO_CONVERTERS so they become URL path params, not body forms.)
    @rpc(atomic_requests=False)
    def post_only(request: HttpRequest) -> None:
        pass

    @rpc(methods=["GET", "POST"], atomic_requests=False)
    def get_allowed(request: HttpRequest) -> None:
        pass

    request = rf.get(f"/{rpc.handlers['rpc_post_only']['url']}")
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_post_only"]["handler"](request)
    assert response.status_code == 405

    request = rf.get(f"/{rpc.handlers['rpc_get_allowed']['url']}")
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_get_allowed"]["handler"](request)
    assert response.status_code == 200

    request = rf.post(
        f"/{rpc.handlers['rpc_post_only']['url']}",
        data="null",
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_post_only"]["handler"](request)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_form_required_validation(rf: Any) -> None:
    rpc = Router()

    @rpc(atomic_requests=False)
    def required_test(request: Any, form: RequiredTestForm) -> str:
        return "ok"

    # All filled -> 200
    request = rf.post(
        f"/{rpc.handlers['rpc_required_test']['url']}",
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
    response = await rpc.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 200

    # Empty explicit_required -> 400
    request = rf.post(
        f"/{rpc.handlers['rpc_required_test']['url']}",
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
    response = await rpc.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 400
    errors = json.loads(response.content)
    assert any(e["loc"] == ["explicit_required"] for e in errors)

    # Empty explicit_optional + filled required fields -> 200
    request = rf.post(
        f"/{rpc.handlers['rpc_required_test']['url']}",
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
    response = await rpc.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 200

    # Empty inferred_required -> 400
    request = rf.post(
        f"/{rpc.handlers['rpc_required_test']['url']}",
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
    response = await rpc.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 400
    errors = json.loads(response.content)
    assert any(e["loc"] == ["inferred_required"] for e in errors)

    # None for inferred_optional + filled required fields -> 200
    request = rf.post(
        f"/{rpc.handlers['rpc_required_test']['url']}",
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
    response = await rpc.handlers["rpc_required_test"]["handler"](request)
    assert response.status_code == 200

    # Read-only fields are set to None regardless of client input
    @rpc(atomic_requests=False)
    def read_only_test(request: Any, form: ReadOnlyTestForm) -> str:
        assert form.editable == "value"
        assert form.read_only_field is None
        assert form.optional_field is None
        return "ok"

    request = rf.post(
        f"/{rpc.handlers['rpc_read_only_test']['url']}",
        data=json.dumps({"editable": "value"}),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_read_only_test"]["handler"](request)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_sync_rpc_rolls_back_on_errors(rf: Any) -> None:
    rpc = Router()

    # Use list[str] because bare str is a DJANGO_CONVERTER (URL path param).
    @rpc()
    def sync_expected(request: HttpRequest, form: list[str]) -> None:
        User.objects.create(username=form[0], email=form[0])
        raise AssertionError("Expected")

    @rpc()
    def sync_unexpected(request: HttpRequest, form: list[str]) -> None:
        User.objects.create(username=form[0], email=form[0])
        1 / 0

    generate_server_schema()

    expected_email = unique_email()
    request = rf.post(
        f"/{rpc.handlers['rpc_sync_expected']['url']}",
        data=json.dumps([expected_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()

    response = await rpc.handlers["rpc_sync_expected"]["handler"](request)
    assert response.status_code == 400
    assert not await sync_to_async(User.objects.filter(email=expected_email).exists)()

    unexpected_email = unique_email()
    request = rf.post(
        f"/{rpc.handlers['rpc_sync_unexpected']['url']}",
        data=json.dumps([unexpected_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    with pytest.raises(ZeroDivisionError):
        await rpc.handlers["rpc_sync_unexpected"]["handler"](request)
    assert not await sync_to_async(User.objects.filter(email=unexpected_email).exists)()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_async_rpc_does_not_roll_back_on_errors(rf: Any) -> None:
    rpc = Router()

    @rpc()
    async def async_expected(request: HttpRequest, form: list[str]) -> None:
        await sync_to_async(User.objects.create)(username=form[0], email=form[0])
        raise AssertionError("Expected")

    @rpc()
    async def async_unexpected(request: HttpRequest, form: list[str]) -> None:
        await sync_to_async(User.objects.create)(username=form[0], email=form[0])
        1 / 0

    async_expected_email = unique_email()
    request = rf.post(
        f"/{rpc.handlers['rpc_async_expected']['url']}",
        data=json.dumps([async_expected_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_async_expected"]["handler"](request)
    assert response.status_code == 400
    assert await sync_to_async(User.objects.filter(email=async_expected_email).exists)()

    async_unexpected_email = unique_email()
    request = rf.post(
        f"/{rpc.handlers['rpc_async_unexpected']['url']}",
        data=json.dumps([async_unexpected_email]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    with pytest.raises(ZeroDivisionError):
        await rpc.handlers["rpc_async_unexpected"]["handler"](request)
    assert await sync_to_async(
        User.objects.filter(email=async_unexpected_email).exists
    )()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_single_model(rf: Any, schema_env: Any) -> None:
    rpc = Router()

    @rpc()
    def get_user_returns(request: Any, form: list[int]) -> ReturnsPick.returns:
        return User.objects.get(id=form[0])

    generate_server_schema(skip_cache=True)

    email = unique_email()
    user = await sync_to_async(User.objects.create)(username=email, email=email)

    request = rf.post(
        f"/{rpc.handlers['rpc_get_user_returns']['url']}",
        data=json.dumps([user.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_get_user_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["id"] == user.id
    assert data["email"] == email


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_list_of_models(rf: Any, schema_env: Any) -> None:
    rpc = Router()

    email1 = unique_email()
    email2 = unique_email()

    @rpc()
    def list_users_returns(
        request: Any, form: list[int]
    ) -> list[ListReturnsPick.returns]:
        return list(User.objects.filter(id__in=form))

    generate_server_schema(skip_cache=True)

    user1 = await sync_to_async(User.objects.create)(username=email1, email=email1)
    user2 = await sync_to_async(User.objects.create)(username=email2, email=email2)

    request = rf.post(
        f"/{rpc.handlers['rpc_list_users_returns']['url']}",
        data=json.dumps([user1.id, user2.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_list_users_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data) == 2
    emails = {item["email"] for item in data}
    assert email1 in emails
    assert email2 in emails


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_returns_nullable(rf: Any, schema_env: Any) -> None:
    rpc = Router()

    @rpc()
    def maybe_user_returns(
        request: Any, form: list[int]
    ) -> NullableReturnsPick.returns | None:
        return User.objects.filter(id=form[0]).first()

    generate_server_schema(skip_cache=True)

    request = rf.post(
        f"/{rpc.handlers['rpc_maybe_user_returns']['url']}",
        data=json.dumps([99999]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_maybe_user_returns"]["handler"](request)

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data is None

    email = unique_email()
    user = await sync_to_async(User.objects.create)(username=email, email=email)
    request = rf.post(
        f"/{rpc.handlers['rpc_maybe_user_returns']['url']}",
        data=json.dumps([user.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_maybe_user_returns"]["handler"](request)

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
    rpc = Router()

    @rpc()
    def get_user_with_score(request: Any, form: list[int]) -> ExtraFieldsPick.returns:
        user = User.objects.get(id=form[0])
        return PickProxy(user, score=42)

    generate_server_schema(skip_cache=True)

    email = unique_email()
    user = await sync_to_async(User.objects.create)(username=email, email=email)

    request = rf.post(
        f"/{rpc.handlers['rpc_get_user_with_score']['url']}",
        data=json.dumps([user.id]),
        content_type="application/json",
    )
    request.user = AnonymousUser()
    response = await rpc.handlers["rpc_get_user_with_score"]["handler"](request)

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

    rpc = Router()

    @rpc(log=True)
    async def observed(request: HttpRequest, form: ObserverInput) -> int:
        if exc:
            raise exc
        return form.value

    generate_server_schema(skip_cache=True)

    request = rf.post(
        f"/{rpc.handlers['rpc_observed']['url']}",
        data={"value": 1},
        content_type="application/json",
    )
    request.user = AnonymousUser()

    if exc:
        with pytest.raises(type(exc)):
            await rpc.handlers["rpc_observed"]["handler"](request)
    else:
        response = await rpc.handlers["rpc_observed"]["handler"](request)
        assert response.status_code == 200

    assert len(calls) == 1
    assert calls[0][0] == RequestStatus[expected_status]
