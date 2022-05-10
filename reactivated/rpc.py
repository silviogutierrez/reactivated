import re
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django import forms
from django.urls import path, reverse, URLPattern, include, URLResolver
from decimal import Decimal
from django.utils import dateparse, timezone
from django.db.models import QuerySet

from typing import (
    Sequence,
    Tuple,
    Dict,
    get_type_hints,
    Any,
    Optional,
    Iterable,
    List,
    NamedTuple,
    Callable,
    TypeVar,
    Type,
    Generic,
    Union,
    TYPE_CHECKING,
    overload,
    cast,
)
from . import Pick, registry, types
from .serialization import create_schema, serialize

THttpRequest = TypeVar("THttpRequest", bound=HttpRequest)

TQuerySet = TypeVar("TQuerySet", bound=Union[Iterable[Any], None])

TFirst = TypeVar("TFirst")

TSecond = TypeVar("TSecond")

TContext = TypeVar("TContext")

TSubcontext = TypeVar("TSubcontext")

TResponse = TypeVar("TResponse")

TForm = TypeVar(
    "TForm", bound=Union[forms.Form, forms.ModelForm[Any], forms.BaseInlineFormSet]
)


if TYPE_CHECKING:
    InputOutput = Tuple[Callable[[TForm], None], Callable[[TForm], TResponse]]
else:
    class InputOutput:
        def __class_getitem__(cls: Type["Undefined"], item: Any) -> Any:
            class InputOutputHolder:
                content = item
            return InputOutputHolder

TView = Union[Callable[[THttpRequest, TForm], TResponse], Callable[[THttpRequest], TResponse], Callable[[THttpRequest], InputOutput[TForm, TResponse]]]


class RPCContext(Generic[THttpRequest, TContext, TFirst, TSecond, TQuerySet]):
    def __init__(
        self,
        context_provider: Callable[[THttpRequest, TFirst, TSecond], TContext],
        authentication: Callable[[HttpRequest], bool],
    ) -> None:
        self.context_provider = context_provider
        self.authentication = authentication
        self.url_path = f"api/functional-rpc-{context_provider.__name__}/"
        self.no_context_url_path = self.url_path
        self.url = f"/{self.url_path}"
        self.routes: List[URLPattern] = []

        instance = []

        url_args = []
        for arg_name, arg_type in get_type_hints(context_provider).items():
            if arg_name in ["request", "return", "queryset"]:
                continue
            instance.append(arg_name)
            url_args.append(f"<{arg_type.__name__}:{arg_name}>")

        self.url_path += "-".join(url_args) + "/"

    @overload
    def process(
        self,
        view: Union[
            Callable[[THttpRequest, TContext], TResponse],
            Callable[[THttpRequest, None], TResponse],
        ],
        *,
        context_provider: Optional[
            Callable[[THttpRequest, TFirst, TSecond], TContext]
        ] = None,
    ) -> URLPattern:
        ...

    @overload
    def process(
        self,
        view: Union[
            Callable[[THttpRequest, TContext, TForm], TResponse],
            Callable[[THttpRequest, None, TForm], TResponse],
        ],
        *,
        context_provider: Optional[
            Callable[[THttpRequest, TFirst, TSecond], TContext]
        ] = None,
    ) -> URLPattern:
        ...

    def process(
        self,
        view: Union[
            Callable[[THttpRequest, TContext], TResponse],
            Callable[[THttpRequest, None], TResponse],
            Callable[[THttpRequest, TContext, TForm], TResponse],
            Callable[[THttpRequest, None, TForm], TResponse],
        ],
        *,
        context_provider: Optional[
            Callable[[THttpRequest, TFirst, TSecond], TContext]
        ] = None,
    ) -> URLPattern:
        pass


class RPC(Generic[THttpRequest]):
    def __init__(self, authentication: Callable[[HttpRequest], bool]) -> None:
        self.authentication = authentication

    def __call__(self, view: TView[THttpRequest, TForm, TResponse]) -> URLPattern:
        return_type = get_type_hints(view)["return"]
        return_schema = create_schema(return_type, registry.definitions_registry)

        def wrapped_view(request: THttpRequest, *args: Any, **kwargs: Any) -> Any:
            if self.authentication(request) is False:
                return HttpResponse("401 Unauthorized", status=401)

            return_value = view(request, *args, **kwargs)  # type: ignore[call-arg]
            data = serialize(return_value, return_schema)
            return JsonResponse(data, safe=False)

        route = path(f"api/functional-rpc-{view.__name__}/", wrapped_view, name=f"rpc_{view.__name__}")
        return route

    def context(
        self,
        context_provider: Union[
            Callable[[THttpRequest, TFirst], TContext],
            Callable[[THttpRequest, TFirst, TSecond], TContext],
        ],
    ) -> RPCContext[THttpRequest, TContext, TFirst, TSecond, None]:
        casted_context_provider = cast(
            Callable[[THttpRequest, TFirst, TSecond], TContext], context_provider
        )

        context = RPCContext[THttpRequest, TContext, TFirst, TSecond, None](
            casted_context_provider, self.authentication
        )
        # self.rpcs.append(context)
        return context


def create_rpc(
    authentication: Callable[[HttpRequest], bool], request_class: Type[THttpRequest]
) -> RPC[THttpRequest]:
    return RPC[THttpRequest](authentication)
