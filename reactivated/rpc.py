from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
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

from . import Pick, registry, types
from .serialization import create_schema, serialize, named_tuple_schema

THttpRequest = TypeVar("THttpRequest", bound=HttpRequest)

TQuerySet = TypeVar("TQuerySet", bound=Union[Iterable[Any], None])

TFirst = TypeVar("TFirst")

TSecond = TypeVar("TSecond")

TContext = TypeVar("TContext")

TSubcontext = TypeVar("TSubcontext")

TResponse = TypeVar("TResponse")

class FormGroup:
    tag: Literal["FormGroup"] = "FormGroup"

    def __init__(self, data: Any = None) -> None:
        for arg_name, arg_type in get_type_hints(self).items():
            setattr(self, arg_name, arg_type(data, prefix=arg_name))


    @property
    def errors(self) -> Any:
        collected = {}

        for arg_name in get_type_hints(self).keys():
            collected[arg_name] = getattr(self, arg_name).errors

        return collected


    def is_valid(self) -> bool:
        return all([getattr(self, arg_name).is_valid() for arg_name in get_type_hints(self).keys()])

    @classmethod
    def get_json_schema(Type, definitions: registry.Definitions) -> registry.Thing:
        return named_tuple_schema(Type, definitions, exclude=["errors"])


TForm = TypeVar(
    "TForm", bound=Union[forms.Form, forms.ModelForm[Any], forms.BaseFormSet, forms.BaseInlineFormSet, FormGroup]
)



if TYPE_CHECKING:
    InputOutput = Tuple[Callable[[TForm], None], Callable[[TForm], TResponse]]
else:

    class InputOutput:
        def __class_getitem__(cls: Type["Undefined"], item: Any) -> Any:
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
        self.url_args_as_params = []
        for arg_name, arg_type in get_type_hints(context_provider).items():
            if arg_name in ["request", "return", "queryset"]:
                continue
            instance.append(arg_name)
            url_args.append(f"<{arg_type.__name__}:{arg_name}>")
            self.url_args_as_params.append((arg_type.__name__, arg_name))

        if url_args:
            self.url_path += "/".join(url_args) + "/"

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

        requires_context = list(get_type_hints(view).values())[1] is not type(None)

        form_type: Optional[Type[forms.BaseForm]] = get_type_hints(view).get("form")
        form_schema = create_schema(form_type or EmptyForm, registry.definitions_registry)
        form_class = form_type or EmptyForm

        def wrapped_view(request: THttpRequest, *args: Any, **kwargs: Any) -> Any:
            if self.authentication(request) is False:
                return HttpResponse("401 Unauthorized", status=401)

            extra_args: Any = {}

            if requires_context is True:
                context = (
                    context_provider(request, *args, **kwargs)
                    if context_provider is not None
                    else self.context_provider(request, *args, **kwargs)
                )
                extra_args["instance"] = context
            else:
                context = None

            form = form_class(
                request.POST if request.method == "POST" else None,
                **extra_args,
            )

            if request.method == "POST":
                if form.is_valid():
                    response = view(request, context, form) if form_type is not None else view(request, context)  # type: ignore[arg-type, call-arg]
                    data = serialize(response, return_schema)

                    return JsonResponse(data, safe=False)
                else:
                    # TODO: this should be code + message, not just messages.
                    # But types will then need to be updated.
                    errors = (
                        form.errors
                        if isinstance(form, forms.BaseFormSet)
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

        input_name = f"{url_name}_input"
        output_name = f"{url_name}_output"
        registry.value_registry[input_name] = form_class
        registry.type_registry[input_name] = form_class  # type: ignore[assignment]
        registry.type_registry[output_name] = return_type
        registry.rpc_registry[url_name] = {
            "url": f"/{self.no_context_url_path}",
            "input": input_name,
            "output": output_name,
            "params": self.url_args_as_params if requires_context else [],
            "type": "form",
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
            if self.authentication(request) is False:
                return HttpResponse("401 Unauthorized", status=401)

            context = self.context_provider(request, *args, **kwargs)

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
    def __init__(self, authentication: Callable[[HttpRequest], bool]) -> None:
        self.authentication = authentication
        self.url_path = "api/functional-rpc/"
        self.url = f"/{self.url_path}"
        self.routes: List[URLPattern] = []
        self.url_args_as_params: List[Tuple[str, str]] = []

    def __call__(self, view: TView[THttpRequest, TForm, TResponse]) -> URLPattern:
        return_type = get_type_hints(view)["return"]
        return_schema = create_schema(return_type, registry.definitions_registry)

        form_type: Optional[Type[forms.BaseForm]] = get_type_hints(view).get(  # type: ignore[assignment]
            "form"
        ) or type(None)
        form_schema = create_schema(form_type, registry.definitions_registry)
        form_class = form_type or EmptyForm

        def wrapped_view(request: THttpRequest, *args: Any, **kwargs: Any) -> Any:
            if self.authentication(request) is False:
                return HttpResponse("401 Unauthorized", status=401)

            if form_type != type(None):  # type: ignore[comparison-overlap]
                form = form_class(
                    # Some forms use positional arguments, like AuthenticationForm
                    data=request.POST if request.method == "POST" else None,
                )

                if request.method == "POST":
                    if form.is_valid():
                        response = view(request, **kwargs, form=form)  # type: ignore[call-arg]
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

            return_value = view(request, *args, **kwargs)
            data = serialize(return_value, return_schema)
            return JsonResponse(data, safe=False)

        url_name = f"rpc_{view.__name__}"
        url_path = f"{self.url_path}rpc_{view.__name__}/"

        # input_name = f"{url_name}_input"
        if form_type != type(None):  # type: ignore[comparison-overlap]
            input_name = f"{url_name}_input"
            registry.type_registry[input_name] = form_type  # type: ignore[assignment]
            registry.value_registry[input_name] = form_class
        else:
            input_name = None

        output_name = f"{url_name}_output"
        registry.type_registry[output_name] = return_type
        registry.rpc_registry[url_name] = {
            "url": f"/{self.url_path}",
            "input": input_name,
            "output": output_name,
            "params": self.url_args_as_params,
            "type": "form_group" if issubclass(form_class, FormGroup) else "form" if issubclass(form_class, forms.BaseForm) else "form_set",
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
    authentication: Callable[[HttpRequest], bool], request_class: Type[THttpRequest]
) -> RPC[THttpRequest]:
    return RPC[THttpRequest](authentication)
