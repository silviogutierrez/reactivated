from typing import Any, NamedTuple, TypeVar

from django import forms
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from .renderer import should_respond_with_json

T = TypeVar("T", bound=NamedTuple)


def template(cls: T) -> T:
    from . import type_registry, template_registry

    type_name = f"{cls.__name__}Props"  # type: ignore[attr-defined]
    type_registry[type_name] = cls  # type: ignore[assignment]
    template_registry[
        cls.__name__  # type: ignore[attr-defined]
    ] = type_name  # type: ignore[assignment]

    class Augmented(cls):  # type: ignore[misc, valid-type]
        def get_serialized(self) -> Any:
            from .serialization import serialize, create_schema

            generated_schema = create_schema(cls, {})
            return serialize(self, generated_schema)

        def render(self, request: HttpRequest) -> TemplateResponse:
            serialized = self.get_serialized()

            return TemplateResponse(
                request, f"{self.__class__.__name__}.tsx", serialized
            )

        def as_json(self, request: HttpRequest) -> JsonResponse:
            return JsonResponse(self.get_serialized())

    Augmented.__name__ = cls.__name__  # type: ignore[attr-defined]
    return Augmented  # type: ignore[return-value]


def interface(cls: T) -> T:
    from . import type_registry

    type_name = f"{cls.__name__}Props"  # type: ignore[attr-defined]
    type_registry[type_name] = cls  # type: ignore[assignment]

    class Augmented(cls):  # type: ignore[misc, valid-type]
        def get_serialized(self) -> Any:
            from .serialization import serialize, create_schema

            generated_schema = create_schema(cls, {})
            return serialize(self, generated_schema)

        def render(self, request: HttpRequest) -> HttpResponse:
            import simplejson

            serialized = simplejson.dumps(self.get_serialized(), indent=4)

            if should_respond_with_json(request):
                return HttpResponse(serialized, content_type="application/json")

            context = self._asdict()
            context_forms = {
                name: possible_form
                for name, possible_form in context.items()
                if isinstance(possible_form, forms.BaseForm)
            }

            return TemplateResponse(
                request,
                "reactivated/interface.html",
                {**self._asdict(), "forms": context_forms, "serialized": serialized},
            )

        def as_json(self, request: HttpRequest) -> JsonResponse:
            return JsonResponse(self.get_serialized())

    Augmented.__name__ = cls.__name__  # type: ignore[attr-defined]
    return Augmented  # type: ignore[return-value]
