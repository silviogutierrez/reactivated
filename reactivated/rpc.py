import enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
    overload,
)

from django import forms
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import URLPattern, path

from . import registry
from .forms import FormGroup as FormGroup
from .serialization import create_schema, serialize

THttpRequest = TypeVar("THttpRequest", bound=HttpRequest)

TQuerySet = TypeVar("TQuerySet", bound=Union[Iterable[Any], None])

TPermission = TypeVar("TPermission", bound=enum.Enum)

TFirst = TypeVar("TFirst")

TSecond = TypeVar("TSecond")

TContext = TypeVar("TContext")

TSubcontext = TypeVar("TSubcontext")

TResponse = TypeVar("TResponse")

TForm = TypeVar(
    "TForm",
    bound=Union[
        forms.Form,
        forms.ModelForm[Any],
        forms.BaseFormSet,
        forms.BaseInlineFormSet,
        FormGroup,
        None,
    ],
)


if TYPE_CHECKING:
    InputOutput = Tuple[Callable[[TForm], None], Callable[[TForm], TResponse]]
    RPCRequest = Union[THttpRequest, TPermission, Literal[False]]
else:

    class RPCRequest:
        def __class_getitem__(cls: Type["RPCRequest"], item: Any) -> Any:
            class RPCRequestHolder:
                permissions = item[1]

            if "RPCPermission" in registry.type_registry:
                assert False
            else:
                registry.type_registry["RPCPermission"] = item[1]
            return RPCRequestHolder

    class InputOutput:
        def __class_getitem__(cls: Type["InputOutput"], item: Any) -> Any:
            class InputOutputHolder:
                content = item

            return InputOutputHolder


TView = Union[
    Callable[[THttpRequest, TForm], TResponse],
    Callable[[THttpRequest], TResponse],
    Callable[[THttpRequest], InputOutput[TForm, TResponse]],
]


class EmptyForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)


class RPCContext(Generic[THttpRequest, TContext, TFirst, TSecond, TQuerySet]):
    def __init__(
        self,
        context_provider: Callable[[THttpRequest, TFirst, TSecond], TContext],
        authentication: Callable[
            [HttpRequest], Union[THttpRequest, enum.Enum, Literal[False]]
        ],
    ) -> None:
        self.context_provider = context_provider
        self.authentication = authentication
        self.url_path = f"api/functional-rpc-{context_provider.__name__}/"
        self.no_context_url_path = self.url_path
        self.url = f"/{self.url_path}"
        self.routes: List[URLPattern] = []

        instance = []

        url_args = []
        self.url_args_as_params = []
        for arg_name, arg_type in get_type_hints(context_provider).items():
            if arg_name in ["request", "return", "queryset"]:
                continue
            instance.append(arg_name)
            url_args.append(f"<{arg_type.__name__}:{arg_name}>")
            self.url_args_as_params.append((arg_type.__name__, arg_name))

        if url_args:
            self.url_path += "/".join(url_args) + "/"

    def context(
        self,
        context_provider: Union[
            Callable[[THttpRequest, TContext], TSubcontext],
            Callable[[THttpRequest, TContext, TFirst], TSubcontext],
            Callable[[THttpRequest, TContext, TFirst, TSecond], TSubcontext],
        ],
    ) -> "RPCContext[THttpRequest, TSubcontext, TFirst, TSecond, None]":
        def inner_context_provider(
            request: THttpRequest, *args: Any, **kwargs: Any
        ) -> Any:
            return context_provider(request, self.context_provider(request, *args, **kwargs))  # type: ignore[call-arg]

        inner_context_provider.__annotations__ = self.context_provider.__annotations__
        inner_context_provider.__name__ = context_provider.__name__

        return RPCContext[THttpRequest, TSubcontext, TFirst, TSecond, None](
            inner_context_provider, self.authentication
        )

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
        return_type = get_type_hints(view)["return"]
        return_schema = create_schema(return_type, registry.definitions_registry)

        form_type: Optional[Type[forms.BaseForm]] = get_type_hints(view).get("form")
        context_type = list(get_type_hints(view).values())[1]

        is_empty_form = issubclass(form_type, type(None)) is True  # type: ignore[arg-type]

        if form_type is None:
            assert False, "Missing form argument"

        create_schema(form_type, registry.definitions_registry)
        form_class = form_type or EmptyForm

        requires_context = issubclass(context_type, type(None)) is False
        requires_instance = (
            requires_context
            and issubclass(form_class, forms.ModelForm)
            and issubclass(form_class.Meta.model, context_type)  # type: ignore[attr-defined]
        )

        def wrapped_view(request: THttpRequest, *args: Any, **kwargs: Any) -> Any:
            authentication_check = self.authentication(request)

            if authentication_check is False:
                return JsonResponse("UNAUTHORIZED", status=401, safe=False)
            elif isinstance(authentication_check, enum.Enum):
                return JsonResponse(authentication_check.name, status=403, safe=False)

            request = authentication_check

            extra_args: Any = {}

            if requires_context is True:
                context = (
                    context_provider(request, *args, **kwargs)  # type: ignore[call-arg]
                    if context_provider is not None
                    else self.context_provider(request, *args, **kwargs)  # type: ignore[call-arg]
                )

                if requires_instance:
                    extra_args["instance"] = context
            else:
                context = None  # type: ignore[assignment]

            if not is_empty_form:
                form_type_hints = get_type_hints(form_class.__init__)
                form_kwargs = extra_args | (
                    {"request": request}
                    if issubclass(form_type_hints.get("request", type), HttpRequest)
                    else {}
                )
                form = form_class(
                    data=request.POST if request.method == "POST" else None,
                    **form_kwargs,
                )
            else:
                form = EmptyForm(data={})

            if request.method == "POST":
                if form.is_valid():
                    try:
                        response = view(request, context, form) if form_type is not None else view(request, context)  # type: ignore[arg-type, call-arg]
                    except forms.ValidationError as error:

                        if hasattr(error, "error_dict"):
                            return JsonResponse(
                                error.message_dict, status=400, safe=False
                            )
                        else:
                            return JsonResponse(
                                {"__all__": [error.message]}, status=400, safe=False
                            )

                    data = serialize(response, return_schema)

                    return JsonResponse(data, safe=False)
                else:
                    # TODO: this should be code + message, not just messages.
                    # But types will then need to be updated.
                    errors = (
                        form.errors
                        if isinstance(form, (forms.BaseFormSet, FormGroup))
                        else {
                            field_name: [error["message"] for error in field_errors]
                            for field_name, field_errors in form.errors.get_json_data().items()
                        }
                    )
                    return JsonResponse(errors, status=400, safe=False)
            else:
                return HttpResponse("", status=405)

        url_name = f"rpc_{view.__name__}"
        url_path = (
            f"{self.url_path}rpc_{view.__name__}/"
            if requires_context is True
            else f"{self.no_context_url_path}rpc_{view.__name__}/"
        )

        if not is_empty_form:
            input_name = f"{url_name}_input"
            registry.value_registry[input_name] = (form_class, False)
            registry.type_registry[input_name] = form_class  # type: ignore[assignment]
        else:
            input_name = None  # type: ignore[assignment]

        output_name = f"{url_name}_output"
        registry.type_registry[output_name] = return_type
        registry.rpc_registry[url_name] = {
            "url": f"/{self.no_context_url_path}",
            "input": input_name,
            "output": output_name,
            "params": self.url_args_as_params if requires_context else [],
            "type": "form_group"
            if issubclass(form_class, FormGroup)
            else "form"
            if issubclass(form_class, forms.BaseForm)
            else "form_set",
        }
        route = path(url_path, wrapped_view, name=url_name)
        return route

    # TODO: merge  RPCContext.rpc() with RPC.__call__()  they are virtually
    # identical. Except wrapped_view here needs to inject the context.
    # And url in the registry is self.no_context_url_path
    def rpc(
        self,
        view: Union[
            Callable[[THttpRequest, TContext], TResponse],
        ],
    ) -> URLPattern:
        return_type = get_type_hints(view)["return"]
        return_schema = create_schema(return_type, registry.definitions_registry)

        def wrapped_view(request: THttpRequest, *args: Any, **kwargs: Any) -> Any:
            authentication_check = self.authentication(request)

            if authentication_check is False:
                return JsonResponse("UNAUTHORIZED", status=401, safe=False)
            elif isinstance(authentication_check, enum.Enum):
                return JsonResponse(authentication_check.name, status=403, safe=False)

            request = authentication_check

            context = self.context_provider(request, *args, **kwargs)  # type: ignore[call-arg]

            return_value = view(request, context)
            data = serialize(return_value, return_schema)
            return JsonResponse(data, safe=False)

        url_name = f"rpc_{view.__name__}"
        url_path = f"{self.url_path}rpc_{view.__name__}/"

        # input_name = f"{url_name}_input"
        input_name = None
        output_name = f"{url_name}_output"
        # registry.type_registry[input_name] = None
        registry.type_registry[output_name] = return_type
        registry.rpc_registry[url_name] = {
            "url": f"/{self.no_context_url_path}",
            "input": input_name,
            "output": output_name,
            "params": self.url_args_as_params,
            "type": "form",
        }
        route = path(url_path, wrapped_view, name=url_name)
        return route


class RPC(Generic[THttpRequest]):
    def __init__(
        self,
        authentication: Callable[
            [HttpRequest], Union[THttpRequest, enum.Enum, Literal[False]]
        ],
    ) -> None:
        self.authentication = authentication
        self.url_path = "api/functional-rpc/"
        self.url = f"/{self.url_path}"
        self.routes: List[URLPattern] = []
        self.url_args_as_params: List[Tuple[str, str]] = []

    def __call__(self, view: TView[THttpRequest, TForm, TResponse]) -> URLPattern:
        return_type = get_type_hints(view)["return"]
        return_schema = create_schema(return_type, registry.definitions_registry)

        form_type: Optional[Type[forms.BaseForm]] = get_type_hints(view).get("form")

        if form_type is None:
            assert False, "Missing form argument"

        is_empty_form = issubclass(form_type, type(None)) is True

        create_schema(form_type, registry.definitions_registry)
        form_class = form_type or EmptyForm

        def wrapped_view(request: THttpRequest, *args: Any, **kwargs: Any) -> Any:
            authentication_check = self.authentication(request)

            if authentication_check is False:
                return JsonResponse("UNAUTHORIZED", status=401, safe=False)
            elif isinstance(authentication_check, enum.Enum):
                return JsonResponse(authentication_check.name, status=403, safe=False)

            request = authentication_check

            if not is_empty_form:
                form_type_hints = get_type_hints(form_class.__init__)
                form_kwargs = (
                    {"request": request}
                    if issubclass(form_type_hints.get("request", type), HttpRequest)
                    else {}
                )

                form = form_class(
                    # Some forms use positional arguments, like AuthenticationForm so
                    # we can't assume the first argument is the POST data.
                    data=request.POST if request.method == "POST" else None,
                    **form_kwargs,  # type: ignore
                )
            else:
                form = EmptyForm(data={})

            if request.method == "POST":
                if form.is_valid():
                    try:
                        response = view(request, **kwargs, form=form)  # type: ignore[call-arg]
                    except forms.ValidationError as error:
                        if hasattr(error, "error_dict"):
                            return JsonResponse(
                                error.message_dict, status=400, safe=False
                            )
                        else:
                            return JsonResponse(
                                {"__all__": [error.message]}, status=400, safe=False
                            )
                    data = serialize(response, return_schema)

                    return JsonResponse(data, safe=False)
                else:
                    # TODO: this should be code + message, not just messages.
                    # But types will then need to be updated.
                    errors = (
                        form.errors
                        if isinstance(form, (forms.BaseFormSet, FormGroup))
                        else {
                            field_name: [error["message"] for error in field_errors]
                            for field_name, field_errors in form.errors.get_json_data().items()
                        }
                    )
                    return JsonResponse(errors, status=400, safe=False)
            else:
                return HttpResponse("", status=405)

        url_name = f"rpc_{view.__name__}"
        url_path = f"{self.url_path}rpc_{view.__name__}/"

        if not is_empty_form:
            input_name = f"{url_name}_input"
            registry.type_registry[input_name] = form_type  # type: ignore[assignment]
            registry.value_registry[input_name] = (form_class, False)
        else:
            input_name = None  # type: ignore[assignment]

        output_name = f"{url_name}_output"
        registry.type_registry[output_name] = return_type
        registry.rpc_registry[url_name] = {
            "url": f"/{self.url_path}",
            "input": input_name,
            "output": output_name,
            "params": self.url_args_as_params,
            "type": "form_group"
            if issubclass(form_class, FormGroup)
            else "form"
            if issubclass(form_class, forms.BaseForm)
            else "form_set",
        }
        route = path(url_path, wrapped_view, name=url_name)
        return route

    def context(
        self,
        context_provider: Union[
            Callable[[THttpRequest], TContext],
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
    authentication: Callable[
        [HttpRequest], Union[THttpRequest, enum.Enum, Literal[False]]
    ]
) -> RPC[THttpRequest]:
    return RPC[THttpRequest](authentication)
