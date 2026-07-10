from __future__ import annotations

__all__ = ["InlinePick", "PickArgs"]

import ast
import contextlib
import datetime
import decimal
import enum
import hashlib
import importlib
import inspect
import json
import logging
import os
import pathlib
import site
import subprocess
import sys
import traceback
import uuid
import zoneinfo
from types import GenericAlias, ModuleType, NoneType, UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Coroutine,
    Generic,
    Literal,
    NamedTuple,
    NotRequired,
    Protocol,
    Sequence,
    Type,
    TypedDict,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from asgiref.sync import sync_to_async
from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.db import models as dj_models
from django.db import transaction
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.functional import LazyObject
from django.utils.html import escape
from pydantic._internal import _generate_schema

import reactivated.rpc.patches  # noqa: F401

if TYPE_CHECKING:
    from ..forms.schema import FieldDescriptor
from pydantic import (
    BaseModel,
    ConfigDict,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    computed_field,
    create_model,
    model_validator,
    with_config,
)
from pydantic.functional_validators import ModelWrapValidatorHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing_extensions import ParamSpec

from reactivated.fields import _EnumField
from reactivated.stubs import _GenericAlias
from reactivated.utils import ClassLookupDict

from ..registry import Thing
from ..transport import DJANGO_CONVERTERS, url_segment
from .utils import module_name_to_app_name


class ScopeDenied:
    """A scope failure on an rpc chain: False or an HttpResponse, both
    coerced to the uniform denial. The discarded value is kept for the
    DEBUG log so an unexpected 401 is never a mystery."""

    def __init__(self, discarded: Any) -> None:
        self.discarded = discarded


FieldSegment = tuple[str, bool, bool]


class FieldDescriptorWrapper(NamedTuple):
    descriptor: FieldDescriptor
    target_name: str | None = None
    annotation: Any | None = None


def get_field_descriptor(
    pick_name: str, model_class: type[dj_models.Model], field_chain: list[str]
) -> tuple[FieldDescriptorWrapper, Sequence[FieldSegment]]:
    from ..models import ComputedRelation

    field_name, *remaining = field_chain

    resolved_hints = (
        model_class.resolve_type_hints()
        if hasattr(model_class, "resolve_type_hints")
        else {}
    )

    try:
        overrides = get_type_hints(model_class, localns=resolved_hints)
        annotation = overrides.get(field_name, None)

        field_descriptor = (
            FieldDescriptorWrapper(
                descriptor=model_class._meta.pk, annotation=annotation, target_name="pk"
            )
            if field_name == "pk"
            else FieldDescriptorWrapper(
                descriptor=model_class._meta.get_field(field_name),  # type: ignore[arg-type]
                annotation=annotation,
            )
        )
    except FieldDoesNotExist as e:
        possible_method_or_property = getattr(model_class, field_name, None)

        if isinstance(possible_method_or_property, ComputedRelation):
            field_descriptor = FieldDescriptorWrapper(
                descriptor=possible_method_or_property
            )
        elif possible_method_or_property is not None:
            # TODO: stronger checks here. This could just be a random method with
            # more than the `self` argument. Which would fail at runtime.
            possible_method, is_callable = (
                (possible_method_or_property.fget, False)
                if isinstance(possible_method_or_property, property)
                else (possible_method_or_property, True)
            )
            annotations = get_type_hints(
                possible_method, localns=resolved_hints, include_extras=True
            )

            field_descriptor = FieldDescriptorWrapper(
                descriptor=schema_module().ComputedField(
                    name=field_name,
                    annotation=annotations["return"],
                    is_callable=is_callable,
                )
            )
        else:
            raise e

    if isinstance(
        field_descriptor.descriptor,
        (
            dj_models.ForeignKey,
            dj_models.OneToOneField,
            dj_models.ManyToManyField,
            dj_models.ManyToOneRel,
            ComputedRelation,
            # TODO: Maybe RelatedField replaces all of the above?
            dj_models.fields.related.RelatedField,
        ),
    ):
        if len(remaining) == 0:
            if isinstance(field_descriptor.descriptor, ForeignObjectRel):
                assert False, (
                    f"You cannot Pick reverse relationships. Specify which fields from {field_name} you want, such as {field_name}.example_field"
                )

            if (
                isinstance(field_descriptor.descriptor, (dj_models.ForeignKey))
                and field_name == field_descriptor.descriptor.attname
            ):
                copy = field_descriptor.descriptor.foreign_related_fields[0].__class__(
                    null=field_descriptor.descriptor.null
                )

                return (
                    FieldDescriptorWrapper(
                        descriptor=copy,
                        target_name=field_name,
                        annotation=None,
                    ),
                    (),
                )

            assert False, (
                f"Do not specify related fields directly for model {model_class} in {pick_name}. Use {field_name}_id if you just want the reference or {field_name}.subfield if you want fields inside the related model"
            )

        nested_descriptor, nested_field_names = get_field_descriptor(
            pick_name,
            field_descriptor.annotation or field_descriptor.descriptor.related_model,  # type: ignore[arg-type]
            remaining,
        )

        # TODO: Maybe RelatedField replaces all of the above?
        # Consolidate around many_* properties
        # OneToOneRel is a subclass of ManyToOneRel so we need to short circuit.
        is_multiple = (
            not isinstance(field_descriptor.descriptor, dj_models.OneToOneRel)
            and isinstance(
                field_descriptor.descriptor,
                (dj_models.ManyToManyField, dj_models.ManyToOneRel),
            )
        ) or field_descriptor.descriptor.many_to_many is True

        # Note: OneToOneRel, like EmailUser.profile could technically be null.
        # In Django world, it throws an exception.  But when serializing, we
        # always assume null unless manually annotated say, for user profile
        # because we always know it's not null.
        is_null = (
            isinstance(field_descriptor.descriptor, dj_models.OneToOneRel)
            and field_descriptor.annotation is None
        ) or (
            isinstance(
                field_descriptor.descriptor, (dj_models.ForeignKey, ComputedRelation)
            )
            and field_descriptor.descriptor.null is True
        )

        return (
            nested_descriptor,
            ((field_name, is_multiple, is_null), *nested_field_names),
        )
    elif len(remaining) == 0:
        return field_descriptor, ()

    assert False, "Unknown descriptor"


def schema_module() -> Any:  # lazy: breaks the forms<->core cycle
    from ..forms import schema

    return schema


logger = logging.getLogger("django.server")


RPC_PREFIX = "rpc"

TS_TYPE_MAP: dict[type, str] = {int: "number", str: "string", uuid.UUID: "UUID"}

RPCInput = ParamSpec("RPCInput")

RPCOutput = TypeVar("RPCOutput")


def typed_not_yet_working_rpc(
    func: Callable[RPCInput, RPCOutput],
) -> Callable[RPCInput, RPCOutput]:
    def wrapper(*args: RPCInput.args, **kwds: RPCInput.kwargs) -> RPCOutput:
        return func(*args, **kwds)

    return wrapper


RPCExport = TypeVar("RPCExport")
TExported = TypeVar("TExported")


PRIMITIVES = (str, int, float, bool, type(None))


def _validate_primitive(value: Any, owner: str) -> None:
    if isinstance(value, enum.Enum) or isinstance(value, PRIMITIVES):
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_primitive(item, owner)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_primitive(key, owner)
            _validate_primitive(item, owner)
        return
    raise TypeError(
        f"export: {owner} contains {type(value).__name__}, which is not a "
        f"primitive. Exported values are str/int/float/bool/None, lists, "
        f"tuples, dicts, and enum members — nothing else."
    )


def _register_export(cls: Any, name: str | None, caller_frame: Any) -> None:
    if inspect.isclass(cls):
        if name is None and (prefix := module_name_to_app_name(cls.__module__)) is None:
            assert False, f"Could not find app name for {cls}"
        registry_name = name or f"{prefix}.{cls.__qualname__}"
        if registry_name in manually_exported_registry:
            raise TypeError(f"export: duplicate name {registry_name!r}")
        manually_exported_registry[registry_name] = cls
        if issubclass(cls, enum.Enum):
            # Enums always ship both the type and the runtime value map.
            # Labels that are secrets don't belong in an exported enum —
            # export a Literal of the safe values instead.
            value_registry[registry_name] = cls
        return

    if get_origin(cls) is Literal or isinstance(cls, UnionType):
        assert caller_frame is not None
        caller_module = inspect.getmodule(caller_frame)
        module_name = caller_module.__name__ if caller_module else None
        if name is not None:
            registry_name = name
        else:
            possible_name = [
                var_name
                for var_name, var_val in caller_frame.f_locals.items()
                if var_val is cls
            ][0]
            if (
                module_name
                and (app_name := module_name_to_app_name(module_name))
                and possible_name
            ):
                registry_name = f"{app_name}.{possible_name}"
            else:
                assert False, f"Problem finding name for {cls}"
        if registry_name in manually_exported_registry:
            raise TypeError(f"export: duplicate name {registry_name!r}")
        manually_exported_registry[registry_name] = cls
        return

    # A module-level value: primitives only, typed by its annotation.
    assert caller_frame is not None
    caller_module = inspect.getmodule(caller_frame)
    module_name = caller_module.__name__ if caller_module else None
    matches = [
        var_name
        for var_name, var_val in caller_frame.f_locals.items()
        if var_val is cls
    ] or [
        var_name
        for var_name, var_val in caller_frame.f_globals.items()
        if var_val is cls
    ]
    var_name = matches[0] if matches else None
    if name is None and (var_name is None or module_name is None):
        raise TypeError(f"export: could not resolve a name for {cls!r} — pass name=...")
    # App-path resolution is deferred to generation time: values are often
    # exported at module scope during app loading, before the registry is
    # ready. The key here is the raw (module, name) pair.
    registry_name = name or f"{module_name}:{var_name}"
    _validate_primitive(cls, registry_name)
    if registry_name in exported_values_registry:
        raise TypeError(f"export: duplicate name {registry_name!r}")
    annotation = (
        caller_frame.f_globals.get("__annotations__", {}).get(var_name)
        if var_name is not None
        else None
    )
    exported_values_registry[registry_name] = (cls, annotation)


@overload
def export(*, name: str | None = None) -> Callable[[RPCExport], RPCExport]: ...


@overload
def export(arg: TExported, *, name: str | None = None) -> TExported: ...


def export(arg: Any = None, *, name: str | None = None) -> Any:
    """The one export: Picks and Enums (decorator or direct), Literal/union
    aliases, and module-level primitive values. Enums always emit type and
    value map; values are typed by their annotation when present."""
    if arg is not None:
        _register_export(
            arg,
            name,
            inspect.currentframe().f_back,  # type: ignore[union-attr]
        )
        return arg

    def inner(cls: RPCExport) -> RPCExport:
        _register_export(
            cls,
            name,
            inspect.currentframe().f_back,  # type: ignore[union-attr]
        )
        return cls

    return inner


def serialize_exception(e: Exception) -> dict[str, Any]:
    return {
        "type": type(e).__name__,
        "message": str(e),
        "args": e.args,
        "traceback": traceback.format_exc(),
    }


CUSTOM_MESSAGES = {
    "string_too_short": "This field is required",
    "missing": "This field is required",
}


def process_errors(validation_error: ValidationError) -> Any:
    converted = []

    for error in json.loads(validation_error.json()):
        if error["type"] in ["value_error", "assertion_error"]:
            # EmailStr
            if "reason" in error["ctx"]:
                error["msg"] = error["ctx"]["reason"]
            else:
                error["msg"] = error["ctx"]["error"]

        if custom_message := CUSTOM_MESSAGES.get(error["type"]):
            ctx = error.get("ctx")
            error["msg"] = custom_message.format(**ctx) if ctx else custom_message
        converted.append(error)

    return converted


def form_from_type_adapter(type_adapter: TypeAdapter[Any]) -> Type[forms.Form]:
    form_fields = {}

    for field_name, _ in type_adapter.json_schema().get("properties", {}).items():
        if field_name == "description":
            form_fields[field_name] = forms.CharField(widget=forms.Textarea)
        else:
            form_fields[field_name] = forms.CharField()

    form_class = type("Form", (forms.Form,), form_fields)
    return form_class


RPCCall = TypeVar("RPCCall", bound=Callable[..., Any])

THttpRequest = TypeVar("THttpRequest", bound=HttpRequest)
TAnonymous = TypeVar("TAnonymous", bound=HttpRequest)
# The principal: whatever the access function returns on success — a user, a
# NewType-minted proof (e.g. StaffUser), or the request itself. The framework
# never inspects it; it is passed to the handler as its first parameter.
TPrincipal = TypeVar("TPrincipal")

RPCAccess = Callable[[TAnonymous], Awaitable[TPrincipal | Literal[False]]]


async def anyone(request: THttpRequest) -> "THttpRequest | Literal[False]":
    """Identity access: no check runs and the request itself is the principal,
    so handlers keep the classic (request, form) signature. For endpoints that
    are deliberately public long-term, prefer a named access function in your
    project's access module — same body, documented intent."""
    return request


class RPCDecorator(Protocol[TPrincipal]):
    def __call__(
        self, rpc_call: Callable[Concatenate[TPrincipal, RPCInput], RPCOutput]
    ) -> Callable[Concatenate[TPrincipal, RPCInput], RPCOutput]: ...


def build_rpc_decorator(
    handlers: dict[str, "RPC"],
    *,
    scope_adapter: "Any | None" = None,
    access: "RPCAccess[Any, Any] | None" = None,
    csrf_exempt: bool = False,
    log: Literal["errors"] | bool = False,
    atomic_requests: bool = True,
    is_query: bool = False,
    methods: list[Literal["GET", "POST"]] | None = None,
) -> RPCDecorator[Any]:
    def decorator(rpc_call: RPCCall) -> RPCCall:
        rpc_name = f"{RPC_PREFIX}_{rpc_call.__name__}"
        sig = inspect.signature(rpc_call)
        rpc_hints = get_type_hints(rpc_call)
        rpc_output = rpc_hints["return"]

        # Classify params by type
        rpc_params: list[tuple[type, str]] = []
        rpc_form = None
        rpc_form_name: str | None = None
        # Parameters typed HttpRequest (beyond the principal slot) are
        # injected by the framework and excluded from the client schema.
        request_params: list[str] = []

        for param_index, (param_name, param) in enumerate(sig.parameters.items()):
            # The first parameter is always the principal (whatever the
            # access function returned) — positional, name-free, excluded.
            if param_index == 0:
                continue
            if param.default is not inspect.Parameter.empty:
                continue
            param_type = rpc_hints[param_name]
            if isinstance(param_type, type) and issubclass(param_type, HttpRequest):
                request_params.append(param_name)
            elif param_type in DJANGO_CONVERTERS:
                rpc_params.append((param_type, param_name))
            elif param_type is NoneType:
                raise TypeError(
                    f"RPC '{rpc_call.__name__}' has a None-typed param "
                    f"'{param_name}'. Declare a no-body RPC by omitting the "
                    f"param entirely, e.g. def {rpc_call.__name__}(request)."
                )
            else:
                assert rpc_form is None, f"Multiple body params in {rpc_call.__name__}"
                rpc_form = param_type
                rpc_form_name = param_name

        if scope_adapter is not None:
            rpc_params = list(scope_adapter.chain_params) + rpc_params

        # Build URL
        rpc_url = f"{RPC_PREFIX}/{rpc_call.__name__}/"
        if rpc_params:
            segments = "/".join(url_segment(t, n) for t, n in rpc_params)
            rpc_url = f"{RPC_PREFIX}/{rpc_call.__name__}/{segments}/"

        # Determine HTTP method
        if is_query:
            effective_method: Literal["GET", "POST"] = "GET"
        else:
            effective_method = "POST"

        allowed_methods = methods or [effective_method]

        def get_response(
            *, input: Any, content: Any, status_code: int, is_ui: bool
        ) -> HttpResponse:
            if is_ui is True:
                data = json.dumps(content, indent=4)
                return HttpResponse(
                    f"<html><body><h1>Input</h1><pre>{escape(input)}</pre><h1>Debug response</h1><pre>{escape(data)}</pre></body></html>",
                    status=status_code,
                )
            else:
                return JsonResponse(content, safe=False, status=status_code)

        async def wrapped_rpc_call(request: Any, *args: Any, **kwargs: Any) -> Any:
            import pick_schema  # noqa:F401

            from .observer import RequestStatus, get_observer

            rpc_output_adapter = TypeAdapter(rpc_output)

            async def _notify_observer(
                *,
                status: RequestStatus,
                input: Any = None,
                output: Any = None,
                body: bytes | None = None,
                exception: BaseException | None = None,
            ) -> None:
                observer = get_observer()
                if observer is None:
                    return
                try:
                    await observer(
                        request,
                        rpc_name,
                        log,
                        status,
                        input,
                        output,
                        body,
                        exception,
                    )
                except Exception:
                    logging.getLogger(__name__).exception("RPC observer failed")

            if scope_adapter is not None:
                outcome = await sync_to_async(scope_adapter.run)(request, kwargs)
                if isinstance(outcome, ScopeDenied):
                    logger.debug(
                        "rpc %s: scope failure %r coerced to denied",
                        rpc_name,
                        outcome.discarded,
                    )
                    return JsonResponse({"error": "UNAUTHORIZED"}, status=401)
                access_check = outcome
            else:
                assert access is not None
                access_check = await access(request)

            if access_check is False:
                return JsonResponse({"error": "UNAUTHORIZED"}, status=401)

            principal = access_check

            for request_param in request_params:
                kwargs[request_param] = request

            # --- No-form path ---
            if rpc_form is None:
                if request.method not in allowed_methods:
                    return JsonResponse({"error": "Method not allowed"}, status=405)

                is_async = inspect.iscoroutinefunction(rpc_call)
                try:
                    if is_async:
                        validated_model = await rpc_call(principal, **kwargs)
                    else:

                        @sync_to_async
                        def sync_wrapper() -> Any:
                            maybe_atomic = (
                                transaction.atomic()
                                if atomic_requests
                                else contextlib.nullcontext()
                            )
                            with maybe_atomic:
                                return rpc_call(principal, **kwargs)

                        validated_model = await sync_wrapper()
                except AssertionError as error:
                    await _notify_observer(
                        status=RequestStatus.INVALID,
                        exception=error,
                    )
                    return get_response(
                        input=None,
                        content=list(error.args),
                        status_code=400,
                        is_ui=False,
                    )
                except Exception as error:
                    await _notify_observer(
                        status=RequestStatus.ERROR,
                        exception=error,
                    )
                    raise

                if is_async:
                    output = rpc_output_adapter.dump_python(
                        validated_model, mode="json"
                    )
                else:
                    output = await sync_to_async(rpc_output_adapter.dump_python)(
                        validated_model, mode="json"
                    )
                await _notify_observer(status=RequestStatus.SUCCESS, output=output)
                return get_response(
                    input=None, content=output, status_code=200, is_ui=False
                )

            # --- Form path ---
            rpc_form_adapter = TypeAdapter(rpc_form)

            # Handle GET requests for debug UI or when explicitly allowed
            if (
                (settings.DEBUG is True or "GET" in allowed_methods)
                and request.method == "GET"
                or "_rpc_ui" in request.POST
            ):
                form_class = form_from_type_adapter(rpc_form_adapter)

                get_payload = (
                    request.GET
                    if request.method == "GET" and "GET" in allowed_methods
                    else None
                )

                form_instance = form_class(
                    get_payload or request.POST or None, initial=request.GET
                )

                if form_instance.is_valid():
                    data = form_instance.cleaned_data or None
                    is_ui = True and get_payload is None
                else:
                    form_response = render(
                        request, "rpc.html", {"form_instance": form_instance}
                    )
                    return form_response
            # Return 405 for GET requests when not allowed
            elif request.method == "GET":
                return JsonResponse({"error": "Method not allowed"}, status=405)
            else:
                try:
                    data = json.loads(request.body)
                except Exception as error:
                    await _notify_observer(
                        status=RequestStatus.MALFORMED,
                        body=request.body,
                        exception=error,
                    )
                    raise error

                is_ui = False

            try:
                payload = await sync_to_async(rpc_form_adapter.validate_python)(
                    data, context={"user": request.user}
                )
            except ValidationError as validation_error:
                processed = process_errors(validation_error)
                await _notify_observer(
                    status=RequestStatus.INVALID,
                    input=data,
                    output=processed,
                    exception=validation_error,
                )
                return get_response(
                    input=data,
                    content=processed,
                    status_code=400,
                    is_ui=is_ui,
                )

            is_async = inspect.iscoroutinefunction(rpc_call)

            try:
                if is_async:
                    validated_model = await rpc_call(
                        principal, **{str(rpc_form_name): payload}, **kwargs
                    )
                else:

                    @sync_to_async
                    def sync_wrapper() -> Any:
                        maybe_atomic = (
                            transaction.atomic()
                            if atomic_requests
                            else contextlib.nullcontext()
                        )
                        with maybe_atomic:
                            return rpc_call(
                                principal, **{str(rpc_form_name): payload}, **kwargs
                            )

                    validated_model = await sync_wrapper()
            except AssertionError as error:
                await _notify_observer(
                    status=RequestStatus.INVALID,
                    input=data,
                    body=request.body,
                    exception=error,
                )
                return get_response(
                    input=data,
                    content=list(error.args),
                    status_code=400,
                    is_ui=is_ui,
                )
            except Exception as error:
                await _notify_observer(
                    status=RequestStatus.ERROR,
                    input=data,
                    body=request.body,
                    exception=error,
                )
                raise error

            # Serialization must run in sync context for sync handlers
            # because .returns calls model_validate during serialization
            if is_async:
                output = rpc_output_adapter.dump_python(validated_model, mode="json")
            else:
                output = await sync_to_async(rpc_output_adapter.dump_python)(
                    validated_model, mode="json"
                )

            await _notify_observer(
                status=RequestStatus.SUCCESS,
                input=data,
                output=output,
                body=request.body,
            )
            return get_response(
                input=data, content=output, status_code=200, is_ui=is_ui
            )

        if csrf_exempt is True:
            wrapped_rpc_call.csrf_exempt = True  # type: ignore[attr-defined]

        handlers[rpc_name] = {
            "name": rpc_call.__name__,
            "module": rpc_call.__module__,
            "url": rpc_url,
            "input": rpc_form,
            "input_name": rpc_form_name,
            "output": rpc_output,
            "params": rpc_params,
            "method": effective_method,
            "handler": transaction.non_atomic_requests(wrapped_rpc_call),
        }

        return rpc_call

    return decorator


def _get_combined_rpc_registry() -> dict[str, RPC]:
    """Procedures come from MOUNTED routers — what urls.py actually wired —
    so an instantiated-but-unmounted router can no longer emit client
    functions that 404."""
    from ..transport import mounted_routers

    combined: dict[str, RPC] = {}
    for router in mounted_routers:
        handlers = getattr(router, "handlers", None)
        if handlers:
            combined.update(handlers)
    return combined


Override = TypeVar("Override")


PROXIES = ClassLookupDict({})


class BuildContext(NamedTuple):
    module: ast.Module
    imports: set[str]
    built_classes: set[str]


def register(proxied: Type[object]) -> Callable[[Override], Override]:
    def inner(proxy: Override) -> Override:
        PROXIES[proxied] = proxy
        return proxy

    return inner


class AnnotatedType:
    field_type: Any

    @classmethod
    def get_field_type(cls, proxy: Any) -> Any:
        return cls.field_type


class ZoneInfoType(AnnotatedType):
    field_type = zoneinfo.ZoneInfo

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        existing = core_schema.any_schema()

        def serialize(
            value: zoneinfo.ZoneInfo, info: core_schema.SerializationInfo
        ) -> str | zoneinfo.ZoneInfo:
            if info.mode == "json":
                return str(value)
            return value

        existing["serialization"] = core_schema.plain_serializer_function_ser_schema(
            serialize, info_arg=True
        )
        return existing

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
        }


class DurationType(AnnotatedType):
    field_type = datetime.timedelta

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        existing = core_schema.timedelta_schema()

        def serialize(
            value: datetime.timedelta, info: core_schema.SerializationInfo
        ) -> datetime.timedelta | int:
            if info.mode == "json":
                return value.seconds
            return value

        existing["serialization"] = core_schema.plain_serializer_function_ser_schema(
            serialize, info_arg=True
        )
        return existing

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "number",
        }


class UUIDType(AnnotatedType):
    field_type = uuid.UUID

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.uuid_schema()

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "tsType": "UUID",
        }


class PhoneNumberType(AnnotatedType):
    field_type = str

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            lambda v: str(v) if v else "",
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v) if v else "", info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
        }


class LazyStr:
    """
    Custom type for handling Django's LazyObject that resolves to str.
    Used for csrf_token which is a SimpleLazyObject.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(value: Any) -> str:
            if isinstance(value, LazyObject):
                # Resolve the lazy object
                return str(value.__reduce__()[1][0])
            return str(value)

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


class EnumType(AnnotatedType):
    @classmethod
    def get_field_type(cls, proxy: Any) -> Any:
        return proxy.enum

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return handler(source_type)


TOutput = TypeVar("TOutput")


class ReturnsMarker(Generic[TOutput]):
    """
    Generic marker class for Annotated[DjangoModel, ReturnsMarker[OutputPickType]].

    Allows returning Django models directly from rpc handlers with automatic
    serialization via the Pick's output.model_validate.

    Usage in generated schema:
        returns: TypeAlias = Annotated[models.User, ReturnsMarker[UserPick_output]]

    The TOutput type parameter specifies the Pick output class used for serialization.
    """

    def __init__(self, output_type: Type[TOutput]) -> None:
        self.output_type = output_type

    def __class_getitem__(cls, output_type: Type[TOutput]) -> "ReturnsMarker[TOutput]":
        # When used as ReturnsMarker[SomeType], create an instance
        return cls(output_type)

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        output_type = self.output_type

        def serialize(value: Any, info: core_schema.SerializationInfo) -> Any:
            if value is None:
                return None
            validated = output_type.model_validate(value)  # type: ignore[attr-defined]
            return validated.model_dump(mode=info.mode)

        # Accept any value (Django models), serialize via model_validate
        # Don't call handler() on the Django model - we completely take over
        return core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, info_arg=True
            )
        )

    def __get_pydantic_json_schema__(
        self, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        output_type = self.output_type
        if hasattr(output_type, "__pydantic_core_schema__"):
            return handler(output_type.__pydantic_core_schema__)  # type: ignore[attr-defined]

        # Fallback: return empty object schema
        return {"type": "object"}


register(dj_models.BigAutoField)(int)

register(dj_models.AutoField)(int)

register(dj_models.CharField)(str)

register(dj_models.TextField)(str)

register(dj_models.BooleanField)(bool)

register(dj_models.DateField)(datetime.date)

register(dj_models.DateTimeField)(datetime.datetime)

register(dj_models.EmailField)(str)

register(dj_models.IntegerField)(int)

register(dj_models.PositiveIntegerField)(int)

register(dj_models.DecimalField)(decimal.Decimal)

register(dj_models.FloatField)(float)

register(dj_models.UUIDField)(UUIDType)

register(dj_models.DurationField)(DurationType)

register(_EnumField)(EnumType)

register(ArrayField)(list[str])

try:
    from timezone_field import TimeZoneField  # type: ignore[import-not-found]

    register(TimeZoneField)(ZoneInfoType)
except ImportError:
    pass

try:
    from phonenumber_field.modelfields import (  # type: ignore[import-not-found]
        PhoneNumberField,
    )

    register(PhoneNumberField)(PhoneNumberType)
except ImportError:
    pass


class RObject(TypedDict):
    title: str | None
    type: Literal["object"]
    properties: RProperties
    nullable: bool


class RField(TypedDict):
    type: Literal["field"]
    field_class: str
    nullable: bool
    annotation: str | None
    imports: list[str]
    # Set on input schemas for optional_fields: the generated field defaults
    # to None so clients may omit the key entirely (absent means None). The
    # marker lives in the schema, not the codegen call, because nested picks
    # are generated wherever they are first encountered.
    default_none: NotRequired[bool]


class RList(TypedDict):
    type: Literal["list"]
    items: RObject | RField
    nullable: bool


RSchema = RObject | RField | RList

RProperties = dict[str, RSchema]

RDefinitions = dict[str, RSchema]

P = TypeVar("P", bound="Pick")


# Similar to Django Ninja and djantic, we wrap our Django model with this proxy
# class so we can better interpret querysets and related managers.
class ModelToPick:
    def __init__(
        self,
        obj: dj_models.Model | dict[str, Any],
        schema_cls: Type[P],
        context: Any = None,
    ):
        self._obj = obj
        self._schema_cls = schema_cls
        self._context = context

    def __getattr__(self, key: str) -> Any:
        if isinstance(self._obj, dj_models.Model):
            try:
                value = getattr(self._obj, key)
            # Handle OneToOneField reverse relationship. Unlike regular Django,
            # we can't afford to check for exceptions before access. So we
            # assume it can always be nullable unless annotated manually.
            except ObjectDoesNotExist:
                return None

            if isinstance(value, dj_models.Manager):
                value = list(value.all())
        else:
            value = self._obj.get(key, None)

        return value


class PickProxy:
    """Wraps a Django model instance with extra field values.

    Extras are stored in __dict__ (found by default attribute lookup).
    Model fields are delegated via __getattr__.
    """

    def __init__(self, _instance: dj_models.Model, **extras: Any) -> None:
        self._instance = _instance
        self.__dict__.update(extras)

    def __getattr__(self, key: str) -> Any:
        return getattr(self._instance, key)


class _PickProxyToPick:
    """Combines ModelToPick (Manager/OneToOne handling) with PickProxy extras."""

    def __init__(self, model_to_pick: ModelToPick, proxy: PickProxy) -> None:
        self._model_to_pick = model_to_pick
        self._extras = {k: v for k, v in proxy.__dict__.items() if k != "_instance"}

    def __getattr__(self, key: str) -> Any:
        if key in self._extras:
            return self._extras[key]
        return getattr(self._model_to_pick, key)


@with_config(
    ConfigDict(
        from_attributes=True,
    )
)
class PickAsDict(TypedDict):
    @model_validator(mode="wrap")  # type: ignore[misc]
    @classmethod
    def _wrap_model_with_pick(
        cls, values: Any, handler: ModelWrapValidatorHandler[P], info: ValidationInfo
    ) -> Any:
        if isinstance(values, dj_models.Model):
            as_dict = {}

            for field_name in cls[0].__annotations__.keys():
                as_dict[field_name] = getattr(values, field_name)

            return handler(as_dict)
        return handler(values)


class Pick(BaseModel):
    model_config = ConfigDict(from_attributes=True, defer_build=True)

    # For direct Pick without going through pick
    @classmethod
    def get_name(cls) -> str:
        return cls.__qualname__

    @model_validator(mode="wrap")
    @classmethod
    def _wrap_model_with_pick(
        cls, values: Any, handler: ModelWrapValidatorHandler[P], info: ValidationInfo
    ) -> Any:
        if isinstance(values, PickProxy):
            model_pick = ModelToPick(values._instance, cls, info.context)
            values = _PickProxyToPick(model_pick, values)
            return handler(values)
        if isinstance(values, dj_models.Model):
            values = ModelToPick(values, cls, info.context)
            return handler(values)
        return handler(values)

    # Legacy reactivated support
    @classmethod
    def get_serialized_value(cls, value: Any, schema: Thing) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        pick_class = getattr(
            importlib.import_module("pick_schema"),
            schema.schema["title"],
        )
        return pick_class.model_validate(value).model_dump(mode="json")

    @classmethod
    def get_json_schema(cls, definitions: Any) -> Thing:
        schema = cls.model_json_schema(
            mode="serialization", ref_template=f"#/$defs/{cls.__qualname__}_{{model}}"
        )
        defs = schema.pop("$defs", {})
        defs = {f"{cls.__qualname__}_{k}": v for k, v in defs.items()}

        return Thing(
            schema={**schema, "serializer": "reactivated.rpc.core.Pick"},
            definitions={**definitions, **defs},
        )


class PickArgs:
    def __init__(
        self,
        *,
        fields: list[str | tuple[str, Any]],
        read_only_fields: list[str] | None = None,
        write_only_fields: list[str] | None = None,
        extra_fields: dict[str, Any] | None = None,
        as_dict: bool = False,
    ):
        self.fields = fields
        self.read_only_fields = read_only_fields
        self.write_only_fields = write_only_fields
        self.extra_fields = extra_fields
        self.as_dict = as_dict


def _auto_name(model: type, fields: list[str | tuple[str, Any]]) -> str:
    model_name = f"{model.__module__}.{model.__qualname__}"
    fields_str = "_".join(sorted(str(f) for f in fields))
    unhashed = f"{model_name}_{fields_str}"
    hash_val = hashlib.sha1(unhashed.encode("UTF-8")).hexdigest()[:10]
    return f"{model.__qualname__}_{hash_val}"


def _find_existing(
    model: type,
    fields: list[str | tuple[str, Any]],
    extra_fields: dict[str, Any],
    read_only_fields: list[str],
    write_only_fields: list[str],
    as_dict: bool,
) -> type[BasePickHolder] | None:
    for existing in picks_registry:
        if (
            existing.model_class is model
            and existing.fields == fields
            and existing.extra_fields == extra_fields
            and existing.read_only_fields == read_only_fields
            and existing.write_only_fields == write_only_fields
            and existing.as_dict == as_dict
        ):
            return existing
    return None


if TYPE_CHECKING:
    from typing import Annotated as InlinePick
else:

    class InlinePick:
        def __class_getitem__(
            cls, params: tuple[Any, PickArgs | Any]
        ) -> type[BasePickHolder]:
            model, config = params
            frm = inspect.stack()[1]
            mod_name = frm[0].f_globals.get("__name__")
            if mod_name and mod_name in sys.modules:
                mod = sys.modules[mod_name]
            else:
                mod = inspect.getmodule(frm[0])

            if isinstance(config, PickArgs):
                pick_args = config
            elif get_origin(config) is Literal:
                pick_args = PickArgs(fields=list(get_args(config)))
            else:
                raise TypeError(f"Pick expects PickArgs or Literal, got {type(config)}")

            resolved_extra_fields = pick_args.extra_fields or {}
            resolved_read_only = pick_args.read_only_fields or []
            resolved_write_only = pick_args.write_only_fields or []

            existing = _find_existing(
                model,
                pick_args.fields,
                resolved_extra_fields,
                resolved_read_only,
                resolved_write_only,
                pick_args.as_dict,
            )
            if existing is not None:
                return existing

            auto = _auto_name(model, pick_args.fields)

            class PickHolder(BasePickHolder):
                model_class = model
                fields = pick_args.fields
                extra_fields = resolved_extra_fields
                read_only_fields = resolved_read_only
                write_only_fields = resolved_write_only
                as_dict = pick_args.as_dict
                module = mod  # type: ignore[assignment]

                @classmethod
                def get_class_name(holder_cls) -> str:
                    if holder_cls.module is not None:
                        for var_name, var_val in inspect.getmembers(holder_cls.module):
                            if var_val is holder_cls:
                                return var_name
                    return auto

                @classmethod
                def __get_pydantic_core_schema__(
                    holder_cls, source: Any, handler: Any
                ) -> Any:
                    output_type = holder_cls.dereference().output
                    if holder_cls.extra_fields:
                        returns_type = Annotated[PickProxy, ReturnsMarker[output_type]]
                    else:
                        returns_type = Annotated[
                            holder_cls.model_class, ReturnsMarker[output_type]
                        ]
                    return handler.generate_schema(returns_type)

            picks_registry.append(PickHolder)
            return PickHolder


_CP = TypeVar("_CP")


def computed_property() -> Callable[[Callable[..., _CP]], _CP]:
    def decorator(func: Callable[..., _CP]) -> _CP:
        return computed_field(property(func))  # type: ignore[return-value]

    return decorator


TPrimitive = TypeVar("TPrimitive")


# Thin object wrapper around primitives.
# Useful when we need to alias say a string or an untyped status code along with
# NEVER or ERROR or SUBSCRIPTION_REQUIRED.  So string | "NEVER" | "ERROR" |
# "SUBSCRIPTION_REQUIRED" would be problematic to Pydantic and even TypeScript.
# But {value: string} | "NEVER" | "ERROR" | "SUBSCRIPTION_REQUIRED" is not.
class Primitive(PickAsDict, Generic[TPrimitive]):
    value: TPrimitive


def build_nested_schema(
    properties: RProperties, path: Sequence[FieldSegment]
) -> RProperties:
    for item, is_multiple, is_null in path:
        existing_subschema = properties.get(item)

        if is_multiple:
            if existing_subschema is None:
                properties[item] = {
                    "type": "list",
                    "nullable": is_null,
                    "items": {
                        "type": "object",
                        "title": None,
                        "nullable": False,
                        "properties": {},
                    },
                }
            properties = properties[item]["items"]["properties"]  # type: ignore[typeddict-item]
        else:
            if existing_subschema is None:
                properties[item] = {
                    "title": None,
                    "type": "object",
                    "nullable": is_null,
                    "properties": {},
                }

            properties = properties[item]["properties"]  # type: ignore[typeddict-item]

    return properties


def get_field_schema(
    type_class_or_instance: Any,
    *,
    mode: Literal["input", "output"],
    nullable: bool = False,
) -> RField | RObject | RList:
    if type_class_or_instance is None:
        return {
            "type": "field",
            "nullable": False,
            "field_class": "None",
            "imports": [],
            "annotation": None,
        }

    # Unwrap Annotated[X, metadata...] → X before processing.
    if hasattr(type_class_or_instance, "__metadata__"):
        type_class_or_instance = type_class_or_instance.__origin__

    if get_origin(type_class_or_instance) is Literal:
        return {
            "type": "field",
            "nullable": False,
            "field_class": repr(type_class_or_instance),
            "imports": [type_class_or_instance.__module__],
            "annotation": None,
        }

    if isinstance(type_class_or_instance, (GenericAlias, _GenericAlias)):
        if type_class_or_instance.__origin__ in _generate_schema.DICT_TYPES:
            key_schema = get_field_schema(
                type_class_or_instance.__args__[0],
                mode=mode,
            )
            key_name = key_schema["field_class"]  # type: ignore[typeddict-item]
            value_schema = get_field_schema(
                type_class_or_instance.__args__[1],
                mode=mode,
            )
            value_name = value_schema.get("title", value_schema.get("field_class"))
            value_name = (
                f"{value_name} | None" if value_schema["nullable"] else value_name
            )

            return {
                "type": "field",
                "nullable": nullable,
                "field_class": f"dict[{key_name}, {value_name}]",
                "imports": [*key_schema["imports"]],  # type: ignore[typeddict-item]
                "annotation": None,
            }
        if type_class_or_instance.__origin__ in _generate_schema.LIST_TYPES:
            items = get_field_schema(
                type_class_or_instance.__args__[0],
                mode=mode,
            )
            assert items["type"] != "list"

            return {
                "type": "list",
                "nullable": nullable,
                "items": items,
            }

        return {
            "type": "field",
            "nullable": False,
            "field_class": repr(type_class_or_instance),
            "imports": [],
            "annotation": None,
        }

    if inspect.isclass(type_class_or_instance) and issubclass(
        type_class_or_instance, BasePickHolder
    ):
        pick_schema = type_class_or_instance.get_schema(
            {},
            mode=mode,
        )
        return {**pick_schema, "nullable": nullable}

    if isinstance(type_class_or_instance, UnionType):
        args = type_class_or_instance.__args__
        non_none_args = [a for a in args if a is not NoneType]
        has_none = len(non_none_args) < len(args)

        if len(non_none_args) == 1:
            return get_field_schema(non_none_args[0], mode=mode, nullable=True)

        # Multi-type union: resolve each member and join as "A | B | C".
        parts: list[str] = []
        all_imports: list[str] = []
        for arg in non_none_args:
            sub = get_field_schema(arg, mode=mode)
            assert sub["type"] == "field"
            parts.append(sub["field_class"])
            all_imports.extend(sub.get("imports", []))

        return {
            "type": "field",
            "nullable": has_none or nullable,
            "field_class": " | ".join(parts),
            "imports": all_imports,
            "annotation": None,
        }

    # Model field descriptors are instances, so we need the class from the descriptor.
    type_class = (
        type_class_or_instance
        if isinstance(type_class_or_instance, type)
        else type_class_or_instance.__class__
    )

    # Let Pydantic handle it. It will complain if the class is not
    # supported.
    try:
        proxy = PROXIES[type_class]
    except KeyError:
        return {
            "type": "field",
            "nullable": nullable,
            "field_class": f"{type_class.__module__}.{type_class.__qualname__}",
            "imports": [type_class.__module__],
            "annotation": None,
        }

    imports = []
    annotation = None

    if issubclass(proxy, AnnotatedType):
        annotation = f"{proxy.__module__}.{proxy.__qualname__}"
        imports.append(proxy.__module__)
        proxy = proxy.get_field_type(type_class_or_instance)

    schema = get_field_schema(proxy, nullable=nullable, mode=mode)

    assert schema["type"] == "field"

    return {
        **schema,
        "annotation": annotation,
        "imports": [*schema["imports"], *imports],
    }


# Crude, should actually dereference instead of comparing names.
# This is very useful for narrowing mixed RPC inputs.
class RefMeta(type):
    def __instancecheck__(self, instance: Any) -> bool:
        return self.get_name() == instance.__class__.__name__  # type: ignore[no-any-return,attr-defined]


class Ref(metaclass=RefMeta):
    pass


class BasePickHolder:
    model_class: Type[dj_models.Model]
    module: ModuleType
    fields: list[str | tuple[str, Any]] = []
    extra_fields: dict[str, Any]
    read_only_fields: list[str]
    write_only_fields: list[str]
    optional_fields: list[str] = []
    as_dict: bool = False

    @classmethod
    def proxy(cls, _instance: dj_models.Model, **kwargs: Any) -> "PickProxy":
        return PickProxy(_instance, **kwargs)

    @classmethod  # type: ignore[misc]
    @property
    def input(cls) -> Any:
        class InputRef(Ref):
            @classmethod  # type: ignore[misc]
            @property
            def Related(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().input.Related  # type: ignore[attr-defined]

            @classmethod
            def get_name(i_cls) -> str:
                return (cls.get_name() or "TODO") + "_input"

            @classmethod
            def model_validate(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().input.model_validate(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def model_json_schema(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().input.model_json_schema(*args, **kwargs)  # type: ignore[attr-defined]

            def __new__(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().input(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def __get_pydantic_core_schema__(i_cls, *args: Any, **kwargs: Any) -> Any:
                # Handle TypedDict / as_dict inputs
                if hasattr(cls.dereference().input, "__annotations__") and hasattr(  # type: ignore[attr-defined]
                    cls.dereference().input,  # type: ignore[attr-defined]
                    "__total__",
                ):
                    handler = args[1]
                    return handler.generate_schema(cls.dereference().input)  # type: ignore[attr-defined]

                return args[1].generate_schema(cls.dereference().input)  # type: ignore[attr-defined]
                # With defer_build=True, we use handler in args[1] instead of recursively calling __get_pydantic_core_schema__
                # return cls.dereference().input.__get_pydantic_core_schema__(  # type: ignore[attr-defined]
                #     *args, **kwargs
                # )

        return InputRef

    @classmethod  # type: ignore[misc]
    @property
    def output(cls) -> Any:
        class OutputRef(Ref):
            @classmethod  # type: ignore[misc]
            @property
            def Related(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().output.Related  # type: ignore[attr-defined]

            @classmethod
            def get_json_schema(i_cls, definitions: Any) -> Thing:
                try:
                    return cls.dereference().output.get_json_schema(definitions)  # type: ignore[no-any-return, attr-defined]
                except ModuleNotFoundError:
                    return Thing(
                        schema={"serializer": "reactivated.rpc.core.BasePickHolder"},
                        definitions=definitions,
                    )

            @classmethod
            def get_name(i_cls) -> str:
                return (cls.get_name() or "TODO") + "_output"

            def __new__(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().output(*args, **kwargs)  # type: ignore[attr-defined]

            # self.wrapped = cls.dereference().output(*args, **kwargs)  # type: ignore[attr-defined]
            # def __init__(self, *args: Any, **kwargs: Any) -> None:
            # self.wrapped = cls.dereference().output(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def model_validate(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().output.model_validate(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def model_json_schema(i_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().output.model_json_schema(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def __get_pydantic_core_schema__(i_cls, *args: Any, **kwargs: Any) -> Any:
                return args[1].generate_schema(cls.dereference().output)  # type: ignore[attr-defined]
                # With defer_build=True, we use handler in args[1] instead of recursively calling __get_pydantic_core_schema__
                # return cls.dereference().output.__get_pydantic_core_schema__(  # type: ignore[attr-defined]
                #     *args, **kwargs
                # )

        OutputRef.__module__ = "reactivated.rpc.core"
        OutputRef.__qualname__ = "Ref"
        return OutputRef

    @classmethod  # type: ignore[misc]
    @property
    def returns(cls) -> Any:
        class ReturnsRef(Ref):
            @classmethod
            def get_name(r_cls) -> str:
                # Same name as output for schema purposes
                return (cls.get_name() or "TODO") + "_output"

            @classmethod
            def get_json_schema(r_cls, definitions: Any) -> Thing:
                try:
                    return cls.dereference().output.get_json_schema(definitions)  # type: ignore[no-any-return, attr-defined]
                except ModuleNotFoundError:
                    return Thing(
                        schema={"serializer": "reactivated.rpc.core.BasePickHolder"},
                        definitions=definitions,
                    )

            def __new__(r_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().output(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def model_validate(r_cls, *args: Any, **kwargs: Any) -> Any:
                return cls.dereference().output.model_validate(*args, **kwargs)  # type: ignore[attr-defined]

            @classmethod
            def __get_pydantic_core_schema__(r_cls, *args: Any, **kwargs: Any) -> Any:
                # Construct Annotated[model_class, ReturnsMarker[output_type]]
                # instead of dereferencing .returns (which may not exist during schema generation)
                output_type = cls.dereference().output  # type: ignore[attr-defined]
                if cls.extra_fields:
                    returns_type: Any = Annotated[PickProxy, ReturnsMarker[output_type]]  # type: ignore[valid-type]
                else:
                    model_cls = cls.model_class
                    returns_type = Annotated[model_cls, ReturnsMarker[output_type]]  # type: ignore[valid-type]
                return args[1].generate_schema(returns_type)

        ReturnsRef.__module__ = "reactivated.rpc.core"
        ReturnsRef.__qualname__ = "Ref"
        return ReturnsRef

    @classmethod
    def get_serialized_value(cls, value: Any, schema: Thing) -> Any:
        return value.model_dump(mode="json")

    @classmethod
    def dereference(cls) -> Type[Pick]:

        schema = importlib.import_module("pick_schema")

        pick_class = getattr(schema, cls.get_name())
        return pick_class  # type: ignore[no-any-return]

    @classmethod
    def model_validate(cls: Type[BasePickHolder], *args: Any, **kwargs: Any) -> Any:
        return cls.dereference().model_validate(*args, **kwargs)

    @classmethod
    def get_class_name(cls: Type[BasePickHolder]) -> str:
        pick_name: str | None = None

        for var_name, var_val in inspect.getmembers(cls.module):
            if (
                isinstance(var_val, type)
                and issubclass(var_val, BasePickHolder)
                and var_val
                is not BasePickHolder  # In case we import BasePickHolder in the same file we use pick
                and var_val.module == cls.module
                and var_val.fields == cls.fields
                and var_val.extra_fields == cls.extra_fields
                and var_val.read_only_fields == cls.read_only_fields
                and var_val.write_only_fields == cls.write_only_fields
                and var_val.optional_fields == cls.optional_fields
                and var_val.model_class is cls.model_class
                and var_val.as_dict == cls.as_dict
            ):
                pick_name = var_name

        assert pick_name is not None, "Could not determine name"

        return pick_name

    @classmethod
    def get_pretty_name(cls: Type[BasePickHolder]) -> str | None:
        for app_config in apps.get_app_configs():
            if app_config.name in cls.module.__name__:
                relative_module = cls.module.__name__.replace(f"{app_config.name}.", "")
                return f"{app_config.label}.{relative_module}.{cls.get_class_name()}"
        return None

    @classmethod
    def get_name(cls: Type[BasePickHolder]) -> str:
        return f"{cls.module.__name__}.{cls.get_class_name()}".replace(".", "_")

    @classmethod
    def get_schema(
        cls: Type[BasePickHolder],
        definitions: RDefinitions,
        *,
        mode: Literal["input", "output"],
    ) -> RObject:
        definition_name = cls.get_name()
        assert definition_name is not None

        schema: RObject = {
            "type": "object",
            "nullable": False,
            "title": (
                f"{definition_name}_input"
                if mode == "input"
                else f"{definition_name}_output"
            ),
            "properties": {},
        }

        for _field_name in cls.fields:
            if isinstance(_field_name, tuple):
                if mode == "input" and _field_name[0] in cls.read_only_fields:
                    continue

                if mode == "output" and _field_name[0] in cls.write_only_fields:
                    continue

                field_name = f"{_field_name[0]}.id"
                field_descriptor, path = get_field_descriptor(
                    definition_name, cls.model_class, field_name.split(".")
                )
                reference = build_nested_schema(schema["properties"], path[:-1])
                target_name, target_is_multiple, target_is_nullable = path[-1]

                if target_is_multiple is True:
                    reference[target_name] = {
                        "type": "list",
                        "items": _field_name[1].get_schema({}, mode=mode),
                        "nullable": target_is_nullable,
                    }
                else:
                    reference[target_name] = _field_name[1].get_schema({}, mode=mode)

                    # TODO: this will cause issues with hashing.
                    reference[target_name]["nullable"] = target_is_nullable
                continue
            else:
                field_name = _field_name

            if mode == "input" and field_name in cls.read_only_fields:
                continue

            if mode == "output" and field_name in cls.write_only_fields:
                continue

            field_descriptor, path = get_field_descriptor(
                definition_name, cls.model_class, field_name.split(".")
            )

            if isinstance(field_descriptor.descriptor, schema_module().ComputedField):
                # TODO: handle no annotation for properties at the Reactivated level
                field_descriptor = field_descriptor._replace(
                    annotation=field_descriptor.descriptor.annotation or Any
                )

                if mode == "input":
                    continue
                #  assert False, "Can't detect nullable for computed field yet"
            else:
                if (
                    mode == "input"
                    and field_descriptor.descriptor.editable is False  # type: ignore[union-attr]
                    # TODO: make this smarter or configurable.
                    and field_descriptor.descriptor.name != "uuid"
                ):
                    continue

            target_name = (
                field_descriptor.target_name or field_descriptor.descriptor.name
            )

            # Computed field is always annotated.
            nullable = (
                False
                if field_descriptor.annotation
                else field_descriptor.descriptor.null  # type: ignore[union-attr]
            )

            reference = build_nested_schema(schema["properties"], path)
            reference[target_name] = get_field_schema(
                field_descriptor.annotation or field_descriptor.descriptor,
                mode=mode,
                nullable=nullable,
            )

            # Nullability and absence of a model default are validated at
            # pick() definition time.
            if mode == "input" and field_name in cls.optional_fields:
                field_reference = reference[target_name]
                assert field_reference["type"] == "field", (
                    "optional_fields only supports scalar model fields"
                )
                field_reference["default_none"] = True
            continue

        for field_name, type_class in cls.extra_fields.items():
            if mode == "input" and field_name in cls.read_only_fields:
                continue

            if mode == "output" and field_name in cls.write_only_fields:
                continue

            extra_field_path, *extra_field_remaining = field_name.split(".")
            extra_reference: RSchema = schema

            while extra_field_remaining:
                if extra_reference["type"] == "object":
                    extra_reference = extra_reference["properties"][extra_field_path]
                elif extra_reference["type"] == "list":
                    assert extra_reference["items"]["type"] == "object"
                    extra_reference = extra_reference["items"]["properties"][
                        extra_field_path
                    ]
                else:
                    assert False

                extra_field_path, *extra_field_remaining = extra_field_remaining

            assert extra_reference["type"] != "field"

            if extra_reference["type"] == "list":
                assert extra_reference["items"]["type"] == "object"
                extra_reference = extra_reference["items"]

            extra_reference["properties"][extra_field_path] = get_field_schema(
                type_class,
                mode=mode,
            )

        return schema


# TODO: I think models_registry is unused?
models_registry: list[Type[BaseModel]] = []
picks_registry: list[Type[BasePickHolder]] = []
manually_exported_registry: dict[str, Type[object]] = {}
# name -> (value, annotation or None)
exported_values_registry: dict[str, tuple[Any, Any]] = {}
value_registry: dict[str, type[enum.Enum]] = {}


class _NamespaceTree:
    """Nested `export namespace` emission. Each contributor addresses a
    dotted path (mirroring the server: app label + relative module +
    name); TS declaration merging keeps contributors independent."""

    def __init__(self) -> None:
        self.children: dict[str, _NamespaceTree] = {}
        self.body: list[str] = []

    def at(self, path: list[str]) -> "_NamespaceTree":
        node = self
        for segment in path:
            node = node.children.setdefault(segment, _NamespaceTree())
        return node

    def render(self, indent: str = "") -> str:
        lines = []
        for line in self.body:
            lines.append(f"{indent}{line}")
        for segment, child in sorted(self.children.items()):
            lines.append(f"{indent}export namespace {segment} {{")
            lines.append(child.render(indent + "    "))
            lines.append(f"{indent}}}")
        return "\n".join(lines)


def _annotation_to_ts(annotation: Any) -> str | None:
    """A deliberately small mapper for exported-value annotations:
    primitives, exported Literal aliases by name, and lists thereof.
    Anything else returns None and the value falls back to `as const`."""
    if annotation is str:
        return "string"
    if annotation in (int, float):
        return "number"
    if annotation is bool:
        return "boolean"
    for key, exported in manually_exported_registry.items():
        if annotation is exported:
            return f"server.{key}"
    origin = get_origin(annotation)
    if origin in (list, tuple):
        args = get_args(annotation)
        if len(args) >= 1:
            inner = _annotation_to_ts(args[0])
            if inner is not None:
                return f"readonly {inner}[]"
    return None


def generate_server_namespace() -> _NamespaceTree:
    tree = _NamespaceTree()
    server = tree.at(["server"])

    # Enums: the const and the type share the leaf name.
    for registry_name, enum_cls in value_registry.items():
        *path, leaf = registry_name.split(".")
        node = server.at(path)
        members = json.dumps(
            {member.name: member.value for member in enum_cls}, indent=4
        )
        node.body.append(f"export const {leaf} = {members} as const;")
        node.body.append(f"export type {leaf} = (typeof {leaf})[keyof typeof {leaf}];")

    # Values: typed by annotation when the mapper knows it, as const otherwise.
    for registry_name, (value, annotation) in exported_values_registry.items():
        if ":" in registry_name:
            module_name, _, var_name = registry_name.partition(":")
            app_name = module_name_to_app_name(module_name)
            if app_name is None:
                raise TypeError(f"export: no app for module {module_name}")
            registry_name = f"{app_name}.{var_name}"
        *path, leaf = registry_name.split(".")
        node = server.at(path)
        ts_type = _annotation_to_ts(annotation) if annotation is not None else None
        serialized = json.dumps(value, indent=4)
        if ts_type is not None:
            node.body.append(f"export const {leaf}: {ts_type} = {serialized};")
        else:
            node.body.append(f"export const {leaf} = {serialized} as const;")

    # Manually exported types: Picks get input/output leaves; everything
    # else (Literal aliases, plain classes) is a type alias at its path.
    emitted_pick_leaves: set[str] = set()
    for registry_name, exported in manually_exported_registry.items():
        if registry_name in value_registry:
            continue  # enums already carry their own type
        *path, leaf = registry_name.split(".")
        node = server.at(path)
        if (
            inspect.isclass(exported)
            and hasattr(exported, "input")
            and hasattr(exported, "output")
        ):
            emitted_pick_leaves.add(registry_name)
            pick_node = node.at([leaf])
            pick_node.body.append(
                f'export type input = Schema["models"]["{registry_name}"]["input"];'
            )
            pick_node.body.append(
                f'export type output = Schema["models"]["{registry_name}"]["output"];'
            )
        else:
            node.body.append(
                f'export type {leaf} = Schema["models"]["{registry_name}"];'
            )

    # Every named pick gets the same leaf, straight from its registration:
    # pick() records module + name, so server.journal.nutrition.Day.output
    # replaces models["journal.nutrition.Day"]["output"]. Anonymous
    # (hash-named) shapes stay reachable only through the models map.
    for pick_holder in picks_registry:
        pretty = pick_holder.get_pretty_name()
        if pretty is None or pretty in emitted_pick_leaves:
            continue
        *path, leaf = pretty.split(".")
        if leaf.startswith("Class_"):
            continue
        emitted_pick_leaves.add(pretty)
        pick_node = server.at([*path, leaf])
        pick_node.body.append(
            f'export type input = Schema["models"]["{pretty}"]["input"];'
        )
        pick_node.body.append(
            f'export type output = Schema["models"]["{pretty}"]["output"];'
        )

    # RPC form definitions live at their module path too; the flat
    # rpcForms map dissolves.
    from ..forms.core import form_registry, get_form_schema

    for form_cls in form_registry:
        app_name = module_name_to_app_name(form_cls.__module__)
        if app_name is None:
            continue
        *path, leaf = f"{app_name}.{form_cls.__qualname__}".split(".")
        node = server.at(path)
        try:
            form_schema = get_form_schema(form_cls)
        except Exception:
            continue
        node.body.append(
            f"export const {leaf} = {json.dumps(form_schema, indent=4)} as const;"
        )
        node.body.append(f"export type {leaf} = typeof {leaf};")

    return tree


class RPC(TypedDict):
    name: str
    module: str
    url: str
    input: Any
    input_name: str | None
    output: Any
    params: list[tuple[type, str]]
    method: Literal["GET", "POST"]
    handler: Callable[..., Coroutine[Any, Any, JsonResponse]]


def pick(
    meta_model: Any,
    *,
    fields: list[str | tuple[str, Any]],
    read_only_fields: list[str] | None = None,
    write_only_fields: list[str] | None = None,
    optional_fields: list[str] | None = None,
    extra_fields: dict[str, Any] | None = None,
    as_dict: bool = False,
) -> Any:
    """Create a typed data shape from a Django model's fields.

    Field visibility and validation are controlled along two independent
    axes:

    Presence (which side a field exists on):
    - read_only_fields: output only, stripped from the input entirely.
    - write_only_fields: input only, stripped from the output entirely.

    Requiredness (whether an input key may be absent):
    - optional_fields: the field exists on both sides, but the input key may
      be omitted and deserializes to None ("absent means None"). The output
      is unaffected: server-side data always has every picked attribute (at
      most its value is null), so "optional" is only meaningful for
      client-to-server payloads. In TypeScript the input key becomes
      `field?: T | null` while the output key stays `field: T | null`.

      This exists for schema evolution: a newly added field would otherwise
      be a required input key, and clients built before the field existed
      (e.g. stale over-the-air bundles) would fail validation by omitting it.

      Restricted to scalar model fields that are nullable and have no model
      default: absent and explicit null are indistinguishable after
      validation (use model_fields_set if a call site needs to tell them
      apart), and a model default would be shadowed by the implicit None.
    """
    for optional_field_name in optional_fields or []:
        optional_descriptor = meta_model._meta.get_field(optional_field_name)
        assert optional_descriptor.null is True, (
            "optional_fields requires a nullable model field: an absent key "
            "deserializes to None, so None must be a legal value"
        )
        assert optional_descriptor.has_default() is False, (
            "optional_fields cannot be combined with a model field default: "
            "an absent key deserializes to None, which would shadow the "
            "model's default"
        )

    flattened_fields = fields
    _extra_fields = extra_fields
    _read_only_fields = read_only_fields
    _write_only_fields = write_only_fields
    _optional_fields = optional_fields
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    _as_dict = as_dict

    class PickHolder(BasePickHolder):
        model_class = meta_model
        fields = flattened_fields
        extra_fields = _extra_fields or {}
        read_only_fields = _read_only_fields or []
        write_only_fields = _write_only_fields or []
        optional_fields = _optional_fields or []
        as_dict = _as_dict
        module = mod  # type: ignore[assignment]

    picks_registry.append(PickHolder)

    return PickHolder


def pick_to_class_def(
    build_context: BuildContext,
    name: str,
    fields: RProperties,
    as_dict: bool = False,
) -> ast.ClassDef | None:

    # TODO: Subtle bug here. Nested classes in tyepddicts that are shared will
    # not be typeddict themselves if they were already built.
    if name in build_context.built_classes:
        return None

    build_context.built_classes.add(name)

    body: list[ast.stmt] = []
    # Track nested types for Related class
    related_fields: dict[str, str] = {}

    module = build_context.module

    for field_name, field_type in fields.items():
        # Captured before the list branch reassigns field_type to its items.
        is_optional = field_type.get("default_none", False)

        # A dict class as a pick class are not considered the same.
        params_for_uniqueness = {"field_type": field_type, "as_dict": as_dict}

        if field_type["type"] == "object":
            title = (
                field_type.get("title")
                or f"Class_{hashlib.md5(json.dumps(params_for_uniqueness).encode()).hexdigest()}"
            )

            nested_class_def = pick_to_class_def(
                build_context,
                title,
                field_type["properties"],
                as_dict=as_dict,
            )

            if nested_class_def is not None:
                module.body.insert(0, nested_class_def)

            type_name = f"{title} | None" if field_type["nullable"] is True else title
            field_annotation = ast.Name(id=type_name, ctx=ast.Load())
            # Track the nested type for Related class
            related_fields[field_name] = title
        elif field_type["type"] == "field":
            title = field_type["field_class"]
            annotation = field_type["annotation"]
            raw_type_name = (
                f"Annotated[{title}, {annotation}]" if annotation is not None else title
            )
            type_name = (
                f"{raw_type_name} | None"
                if field_type["nullable"] is True
                else raw_type_name
            )
            field_annotation = ast.Name(id=type_name, ctx=ast.Load())
            build_context.imports.update(field_type["imports"])
        elif field_type["type"] == "list":
            # TODO: consolidate with field handling above.
            if field_type["items"]["type"] == "field":
                list_field_type = field_type

                field_type = field_type["items"]
                title = field_type["field_class"]
                annotation = field_type["annotation"]
                raw_type_name = (
                    f"Annotated[{title}, {annotation}]"
                    if annotation is not None
                    else title
                )
                type_name = (
                    f"{raw_type_name} | None"
                    if field_type["nullable"] is True
                    else raw_type_name
                )
                build_context.imports.update(field_type["imports"])
                field_annotation = ast.Name(
                    id=(
                        f"list[{type_name}] | None"
                        if list_field_type["nullable"] is True
                        else f"list[{type_name}]"
                    ),
                    ctx=ast.Load(),
                )
            else:
                title = (
                    field_type["items"].get("title")
                    or f"Class_{hashlib.md5(json.dumps(params_for_uniqueness).encode()).hexdigest()}"
                )

                nested_class_def = pick_to_class_def(
                    build_context,
                    title,
                    field_type["items"]["properties"],
                    as_dict=as_dict,
                )

                if nested_class_def is not None:
                    module.body.insert(0, nested_class_def)

                type_name = (
                    f"{title} | None" if field_type["nullable"] is True else title
                )
                field_annotation = ast.Name(id=f"list[{type_name}]", ctx=ast.Load())
                # Track list item type for Related class
                related_fields[field_name] = title
        else:
            assert False, "Invalid type"

        if is_optional and as_dict is True:
            assert isinstance(field_annotation, ast.Name)
            field_annotation = ast.Name(
                id=f"NotRequired[{field_annotation.id}]", ctx=ast.Load()
            )

        body.append(
            ast.AnnAssign(
                target=ast.Name(id=field_name, ctx=ast.Store()),
                annotation=field_annotation,
                value=(
                    ast.Constant(value=None)
                    if is_optional and as_dict is False
                    else None
                ),
                simple=1,
            )
        )

    related_body: list[ast.stmt] = []

    for field_name, field_type_name in related_fields.items():
        # Create a static method that returns the class with proper type annotation
        method_body: list[ast.stmt] = [
            ast.Return(value=ast.Name(id=field_type_name, ctx=ast.Load()))
        ]

        method = ast.FunctionDef(
            name=field_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],  # No arguments for static method
                defaults=[],
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                vararg=None,
            ),
            body=method_body,
            decorator_list=[ast.Name(id="staticmethod", ctx=ast.Load())],
            returns=ast.Subscript(
                value=ast.Name(id="type", ctx=ast.Load()),
                slice=ast.Constant(value=field_type_name),
            ),
            type_params=[],
        )
        related_body.append(method)

    related_class = ast.ClassDef(
        name="Related",
        bases=[],
        keywords=[],
        body=related_body or [ast.Pass()],
        type_params=[],
        decorator_list=[],
    )
    body.append(related_class)

    return ast.ClassDef(
        name=name,
        bases=[
            ast.Name(id="Pick" if as_dict is False else "PickAsDict", ctx=ast.Load())
        ],
        keywords=[],
        body=body,
        type_params=[],
        decorator_list=[],
    )


def _type_to_str(t: Any) -> str:
    """Convert a Python type to its fully-qualified string for codegen.

    Handles plain types, GenericAlias (list[int], tuple[str, str]),
    UnionType (int | None, Foo | None), and Annotated[X, ...] (stripped).
    """
    # Annotated[X, ...] -> just use X
    if get_origin(t) is Annotated:
        return _type_to_str(get_args(t)[0])

    # UnionType: int | None, Foo | None
    if isinstance(t, UnionType):
        parts = [_type_to_str(a) for a in t.__args__]
        return " | ".join(parts)

    # GenericAlias: list[int], tuple[str, str]
    if isinstance(t, GenericAlias):
        origin = _type_to_str(t.__origin__)
        args = ", ".join(_type_to_str(a) for a in t.__args__)
        return f"{origin}[{args}]"

    # typing._GenericAlias (e.g. typing module generics)
    if hasattr(t, "__origin__") and hasattr(t, "__args__"):
        origin = _type_to_str(t.__origin__)
        args = ", ".join(_type_to_str(a) for a in t.__args__)
        return f"{origin}[{args}]"

    # NoneType
    if t is NoneType:
        return "None"

    # PickHolder types (from pick()) - use generated class name
    if isinstance(t, type) and issubclass(t, BasePickHolder):
        return f"{t.get_name()}_output"

    # Plain type with module
    if hasattr(t, "__module__") and hasattr(t, "__qualname__"):
        return f"{t.__module__}.{t.__qualname__}"

    return repr(t)


def _collect_imports_from_type(t: Any, imports: set[str]) -> None:
    """Recursively collect module imports needed by a type."""
    if get_origin(t) is Annotated:
        _collect_imports_from_type(get_args(t)[0], imports)
        return

    if isinstance(t, UnionType):
        for a in t.__args__:
            _collect_imports_from_type(a, imports)
        return

    if isinstance(t, GenericAlias):
        for a in t.__args__:
            _collect_imports_from_type(a, imports)
        return

    if hasattr(t, "__origin__") and hasattr(t, "__args__"):
        for a in t.__args__:
            _collect_imports_from_type(a, imports)
        return

    if t is NoneType:
        return

    if hasattr(t, "__module__") and t.__module__ != "builtins":
        imports.add(t.__module__)


def generate_server_schema(skip_cache: bool = False) -> None:
    # Force-resolve Template annotations to discover inline InlinePick usage.
    # With `from __future__ import annotations`, class body annotations are
    # strings — evaluating them triggers InlinePick.__class_getitem__ which
    # registers picks in picks_registry.
    import sys

    from ..templates import template_registry

    for template_class in template_registry.values():
        template_module = sys.modules[template_class.__module__]
        ns = {**vars(template_module), "__pick_module__": template_module}
        for annotation in template_class.__annotations__.values():
            if isinstance(annotation, str):
                try:
                    eval(annotation, ns)  # noqa: S307
                except Exception:
                    pass

    # Import context processor modules so module-level pick() calls
    # register in picks_registry before we collect pick schemas.
    from django.conf import settings as django_settings
    from django.utils.module_loading import import_string

    for engine in django_settings.TEMPLATES:
        for cp in engine.get("OPTIONS", {}).get("context_processors", []):  # type: ignore[attr-defined]
            import_string(cp)

    module = ast.Module(body=[], type_ignores=[])
    build_context = BuildContext(module=module, imports=set(), built_classes=set())

    pick_schemas: list[
        tuple[str, RObject, RObject, bool, str | None, dict[str, str] | None]
    ] = [
        (
            pick.get_name() or "TODO",
            pick.get_schema({}, mode="input"),
            pick.get_schema({}, mode="output"),
            pick.as_dict,
            (
                f"{pick.model_class.__module__}.{pick.model_class.__name__}"
                if pick.model_class
                else None
            ),
            (
                {
                    name: _type_to_str(t)
                    for name, t in pick.extra_fields.items()
                    if "." not in name
                }
                if pick.extra_fields
                else None
            ),
        )
        for pick in picks_registry
    ]
    # Collect imports from extra_fields types (raw types, not strings).
    for pick_holder in picks_registry:
        if pick_holder.extra_fields:
            for t in pick_holder.extra_fields.values():
                _collect_imports_from_type(t, build_context.imports)

    model_schemas = [
        model.model_json_schema(mode="serialization") for model in models_registry
    ]
    encoded_schema = json.dumps([pick_schemas, model_schemas], indent=2).encode()

    digest = hashlib.sha1(encoded_schema).hexdigest()

    GENERATED_DIRECTORY = getattr(
        settings, "REACTIVATED_SERVER_SCHEMA", site.getsitepackages()[0]
    )

    schema_dir = pathlib.Path(GENERATED_DIRECTORY) / "pick_schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_file = schema_dir / "__init__.py"

    if skip_cache is False and schema_file.exists():
        already_generated = schema_file.read_text()

        if digest in already_generated:
            return

    for (
        schema_title,
        input_schema,
        output_schema,
        as_dict,
        model_class,
        extra_fields_info,
    ) in pick_schemas:
        assert input_schema["title"] is not None
        assert output_schema["title"] is not None
        input_title = input_schema["title"]
        output_title = output_schema["title"]

        input_class_def = pick_to_class_def(
            build_context,
            input_title,
            input_schema["properties"],
            as_dict=as_dict,
        )
        assert input_class_def is not None, (
            "You likely have two picks with identical attributes"
        )
        module.body.append(input_class_def)

        output_class = pick_to_class_def(
            build_context,
            output_title,
            output_schema["properties"],
            as_dict=as_dict,
        )
        assert output_class is not None
        module.body.append(output_class)

        # Build class body with input and output
        class_body: list[ast.stmt] = [
            ast.AnnAssign(
                target=ast.Name(id="input", ctx=ast.Store()),
                annotation=ast.Name(id="TypeAlias", ctx=ast.Load()),
                value=ast.Name(id=input_title, ctx=ast.Store()),
                simple=1,
            ),
            ast.AnnAssign(
                target=ast.Name(id="output", ctx=ast.Store()),
                annotation=ast.Name(id="TypeAlias", ctx=ast.Load()),
                value=ast.Name(id=output_title, ctx=ast.Store()),
                simple=1,
            ),
        ]

        if model_class is not None:
            # model_class is a string like "server.core.models.Profile"
            # Split to get module and class name
            model_class_parts = model_class.rsplit(".", 1)
            model_module = model_class_parts[0]
            model_name = model_class_parts[1]
            build_context.imports.add(model_module)

            # Create AST for module.ClassName (e.g., server.core.models.User)
            model_module_parts = model_module.split(".")
            model_ref: ast.expr = ast.Name(id=model_module_parts[0], ctx=ast.Load())
            for part in model_module_parts[1:]:
                model_ref = ast.Attribute(value=model_ref, attr=part, ctx=ast.Load())
            model_ref = ast.Attribute(value=model_ref, attr=model_name, ctx=ast.Load())

            if extra_fields_info:
                # Generate extras TypedDict
                extras_name = f"{schema_title}_extras"
                extras_body: list[ast.stmt] = []
                for ef_name, ef_type_str in extra_fields_info.items():
                    # With `from __future__ import annotations`, string
                    # annotations work, so we can emit the full type string
                    # directly as an ast.Name.
                    extras_body.append(
                        ast.AnnAssign(
                            target=ast.Name(id=ef_name, ctx=ast.Store()),
                            annotation=ast.Name(id=ef_type_str, ctx=ast.Load()),
                            value=None,
                            simple=1,
                        )
                    )
                extras_class_def = ast.ClassDef(
                    name=extras_name,
                    type_params=[],
                    bases=[ast.Name(id="TypedDict", ctx=ast.Load())],
                    keywords=[],
                    body=extras_body or [ast.Pass()],
                    decorator_list=[],
                )
                module.body.append(extras_class_def)

                # returns uses PickProxy instead of model ref
                class_body.append(
                    ast.AnnAssign(
                        target=ast.Name(id="returns", ctx=ast.Store()),
                        annotation=ast.Name(id="TypeAlias", ctx=ast.Load()),
                        value=ast.Subscript(
                            value=ast.Name(id="Annotated", ctx=ast.Load()),
                            slice=ast.Tuple(
                                elts=[
                                    ast.Name(id="PickProxy", ctx=ast.Load()),
                                    ast.Subscript(
                                        value=ast.Name(
                                            id="ReturnsMarker", ctx=ast.Load()
                                        ),
                                        slice=ast.Name(id=output_title, ctx=ast.Load()),
                                        ctx=ast.Load(),
                                    ),
                                ],
                                ctx=ast.Load(),
                            ),
                            ctx=ast.Load(),
                        ),
                        simple=1,
                    )
                )

                # Generate proxy staticmethod
                proxy_func = ast.FunctionDef(
                    name="proxy",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="_instance", annotation=model_ref)],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=ast.arg(
                            arg="kwargs",
                            annotation=ast.Subscript(
                                value=ast.Name(id="Unpack", ctx=ast.Load()),
                                slice=ast.Name(id=extras_name, ctx=ast.Load()),
                                ctx=ast.Load(),
                            ),
                        ),
                        defaults=[],
                    ),
                    body=[
                        ast.Return(
                            value=ast.Call(
                                func=ast.Name(id="PickProxy", ctx=ast.Load()),
                                args=[ast.Name(id="_instance", ctx=ast.Load())],
                                keywords=[
                                    ast.keyword(
                                        arg=None,
                                        value=ast.Name(id="kwargs", ctx=ast.Load()),
                                    )
                                ],
                            )
                        )
                    ],
                    decorator_list=[ast.Name(id="staticmethod", ctx=ast.Load())],
                    returns=ast.Name(id="PickProxy", ctx=ast.Load()),
                    type_params=[],
                )
                class_body.append(proxy_func)
            else:
                class_body.append(
                    ast.AnnAssign(
                        target=ast.Name(id="returns", ctx=ast.Store()),
                        annotation=ast.Name(id="TypeAlias", ctx=ast.Load()),
                        value=ast.Subscript(
                            value=ast.Name(id="Annotated", ctx=ast.Load()),
                            slice=ast.Tuple(
                                elts=[
                                    model_ref,
                                    ast.Subscript(
                                        value=ast.Name(
                                            id="ReturnsMarker", ctx=ast.Load()
                                        ),
                                        slice=ast.Name(id=output_title, ctx=ast.Load()),
                                        ctx=ast.Load(),
                                    ),
                                ],
                                ctx=ast.Load(),
                            ),
                            ctx=ast.Load(),
                        ),
                        simple=1,
                    )
                )

        class_def = ast.ClassDef(
            name=schema_title,
            type_params=[],
            bases=[],
            keywords=[],
            body=class_body,
            decorator_list=[],
        )
        module.body.append(class_def)

    ns_import_node = ast.Import(
        names=[
            ast.alias(name="builtins", asname=None),
            *[
                ast.alias(name=import_name, asname=None)
                for import_name in build_context.imports
            ],
        ]
    )
    module.body.insert(0, ns_import_node)

    import_node = ast.ImportFrom(
        module="typing",
        names=[
            ast.alias(name="Annotated", asname=None),
            ast.alias(name="NotRequired", asname=None),
            ast.alias(name="TypeAlias", asname=None),
            ast.alias(name="TypedDict", asname=None),
            ast.alias(name="Unpack", asname=None),
        ],
        level=0,
    )
    module.body.insert(0, import_node)

    import_node = ast.ImportFrom(
        module="reactivated.rpc.core",
        names=[
            ast.alias(name="Pick", asname=None),
            ast.alias(name="PickAsDict", asname=None),
            ast.alias(name="PickProxy", asname=None),
            ast.alias(name="ReturnsMarker", asname=None),
        ],
        level=0,
    )
    module.body.insert(0, import_node)

    import_node = ast.ImportFrom(
        module="__future__", names=[ast.alias(name="annotations", asname=None)], level=0
    )
    module.body.insert(0, import_node)

    source_code = "# Digest: %s\n" % digest
    source_code += "# flake8: noqa\n"
    source_code += "# autoflake: skip_file\n"
    source_code += "# isort: skip_file\n"
    source_code += "\n"

    source_code += ast.unparse(ast.fix_missing_locations(module))
    source_code += "\n"

    schema_file.write_text(source_code)
    (schema_dir / "py.typed").write_text("")

    logger.info("Generated rpc server schema")


def generate_client_schema(skip_cache: bool = False) -> None:
    # The server-schema pass just rewrote pick_schema; if this process
    # imported an older version (test sessions, repeated generations),
    # dereference() would read the stale module from sys.modules.
    import pick_schema

    from ..context import get_context_class
    from ..forms.django import register_widgets_in_reactivated
    from ..templates import template_registry

    importlib.reload(pick_schema)

    register_widgets_in_reactivated()

    EXTRA = """
    import {getCookieFromCookieString} from "reactivated/dist/rpc";

    export type RPCResult<TSuccess> = {
        type: "success";
        data: TSuccess;
        // request: Request;
    } | {
        type: "invalid";
        errors: {loc: string[]; msg: string}[];
        // request: Request;
    } | {
        type: "denied";
        reason: unknown;
        // request: Request;
    } | {
        type: "unauthorized";
        // request: Request;
    } | {
        type: "exception";
        exception: unknown;
        // request: Request;
    }

    export type models = Schema["models"];
    """

    CHECKS = ""
    tree = generate_server_namespace()
    server_node = tree.at(["server"])

    # Templates live at server.<app>.templates.<Name>; the type-only
    # Checker block stays flat (erased at build, invisible to consumers).
    if template_registry:
        for template_name, template_class in template_registry.items():
            app_path = module_name_to_app_name(template_class.__module__)
            assert app_path is not None, template_class
            node = server_node.at(app_path.split("."))
            node.body.append(
                f'export type {template_name} = Schema["template_{template_name}"];'
            )
        if "REACTIVATED_SKIP_TEMPLATE_CHECKS" not in os.environ:
            # The prop checks live in their own never-imported file: putting
            # them in schema.tsx gave the schema a type-only edge into every
            # template (which import the schema back), and that cycle made
            # typed-lint inference sensitive to file-processing order —
            # different verdicts per platform.
            CHECKS += "/* eslint-disable */\n"
            CHECKS += 'import type React from "react";\n\n'
            CHECKS += 'import type {Schema} from "./schema";\n\n'
            CHECKS += "type Assert<T extends true> = T;\n"
            CHECKS += "type Accepts<Props, Expected> = [Expected] extends [Props] ? true : false;\n"
            for template_name in template_registry:
                CHECKS += f'import type {{Template as {template_name}Impl}} from "@client/templates/{template_name}";\n'
                CHECKS += f'type _Check{template_name} = Assert<Accepts<React.ComponentProps<typeof {template_name}Impl>, Schema["template_{template_name}"]>>;\n'

    rpc_registry = _get_combined_rpc_registry()

    input_fields = {
        f"{rpc_name}_input": (rpc_call["input"], ...)
        for rpc_name, rpc_call in rpc_registry.items()
        if rpc_call["input"] is not None
    }
    output_fields = {
        f"{rpc_name}_output": (rpc_call["output"], ...)
        for rpc_name, rpc_call in rpc_registry.items()
    }

    for rpc_name, rpc_call in rpc_registry.items():
        call_name = rpc_call["name"]
        rpc_params = rpc_call["params"]
        has_input = rpc_call["input"] is not None
        is_mutation = rpc_call["method"] == "POST"
        rpc_input_name = f"{rpc_name}_input"
        rpc_output_name = f"{rpc_name}_output"

        # Build TS function arguments
        ts_args = []
        if rpc_params:
            param_fields = "; ".join(
                f"{pname}: {TS_TYPE_MAP[ptype]}" for ptype, pname in rpc_params
            )
            ts_args.append(
                f"{{{', '.join(n for _, n in rpc_params)}}}: {{{param_fields}}}"
            )
        if has_input:
            body_param_name = rpc_call["input_name"]
            ts_args.append(f'{body_param_name}: Schema["{rpc_input_name}"]')
        args_str = ", ".join(ts_args)

        # Build URL expression
        base_url = f"/{RPC_PREFIX}/{call_name}"
        if rpc_params:
            param_segments = "/".join(f"${{{n}}}" for _, n in rpc_params)
            url_expr = f"`{base_url}/{param_segments}/`"
        else:
            url_expr = f'"{base_url}/"'

        # Build payload expression
        if has_input:
            payload_expr = rpc_call["input_name"]
        elif is_mutation:
            payload_expr = "{}"
        else:
            payload_expr = "null"

        app_path = module_name_to_app_name(rpc_call["module"])
        assert app_path is not None, rpc_call["module"]
        rpc_node = server_node.at(app_path.split("."))
        rpc_node.body.append(
            f"export async function {call_name}({args_str}) {{\n"
            f'    const {{rpc}} = await import("@reactivated");\n'
            f'    return rpc.requester({url_expr}, {payload_expr}, "{rpc_call["method"]}") as unknown as Promise<RPCResult<Schema["{rpc_output_name}"]>>;\n'
            f"}}"
        )

    model_fields = {
        (f"{model.__module__}.{model.__qualname__}".replace(".", "_")): (model, ...)
        for model in models_registry
    }

    direct_model_fields = {}
    model_fields = {}

    for pick in picks_registry:
        direct_model_fields[pick.input.get_name() or "TODO"] = (  # type: ignore[attr-defined]
            pick.dereference().input,  # type: ignore[attr-defined]
            ...,
        )
        direct_model_fields[pick.output.get_name() or "TODO"] = (  # type: ignore[attr-defined]
            pick.dereference().output,  # type: ignore[attr-defined]
            ...,
        )

        model_fields[pick.get_pretty_name() or pick.get_name()] = (
            create_model(
                pick.get_name() or "TODO",
                input=(pick.dereference().input, ...),  # type: ignore[attr-defined]
                output=(pick.dereference().output, ...),  # type: ignore[attr-defined]
            ),
            ...,
        )
    for exported_model_pretty_name, cls in manually_exported_registry.items():
        model_fields[exported_model_pretty_name] = (cls, ...)  # type: ignore[assignment]

    template_fields = {
        f"template_{template_name}": (template_class, ...)
        for template_name, template_class in template_registry.items()
    }

    # Get the dynamic Context class with all context processor fields
    Context = get_context_class()

    fields = {
        **input_fields,
        **output_fields,
        **direct_model_fields,
        **template_fields,
        "models": (create_model("models", __base__=Pick, **model_fields), ...),  # type: ignore[call-overload]
        "context": (Context, ...),
    }

    Schema = create_model("Schema", **fields)  # type: ignore[call-overload]

    # Generate schema from Pydantic - all refs resolved in one pass
    schema_dict = Schema.model_json_schema(mode="serialization")

    encoded_schema = json.dumps(schema_dict, indent=2)

    GENERATED_DIRECTORY = f"{settings.BASE_DIR}/client/generated"
    # Include forms and constants in digest calculation
    from ..forms import generate_forms_export

    forms_for_digest = generate_forms_export()
    namespace_export = tree.render()
    digest = hashlib.sha1(
        (encoded_schema + EXTRA + forms_for_digest + namespace_export).encode()
    ).hexdigest()
    schema_file = pathlib.Path(GENERATED_DIRECTORY) / "schema.tsx"

    from ..generation import expect

    expect(schema_file)
    if CHECKS:
        expect(schema_file.parent / "checks.tsx")

    if skip_cache is False and schema_file.exists():
        already_generated = schema_file.read_text()

        if digest in already_generated:
            return

    process = subprocess.Popen(
        ["npx", "json2ts", "--additionalProperties", "false"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        cwd=settings.BASE_DIR,
        encoding="utf-8",
    )
    out, error = process.communicate(encoded_schema)

    # Generate forms and constants exports
    from ..forms import generate_forms_export

    forms_export = generate_forms_export()

    from ..generation import write_atomic

    schema_file.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(
        schema_file,
        "\n".join(
            [out, EXTRA, forms_export, namespace_export, "// Digest: %s\n" % digest]
        ),
    )
    if CHECKS:
        write_atomic(schema_file.parent / "checks.tsx", CHECKS)
    logger.info("Generated rpc client schema")
