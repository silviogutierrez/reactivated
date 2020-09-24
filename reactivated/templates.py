from typing import Any, Dict, NamedTuple, Optional, Type, TypeVar

from django import forms
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from .renderer import should_respond_with_json
from .serialization import JSON, create_schema, serialize

T = TypeVar("T", bound=NamedTuple)


class LazySerializationResponse(TemplateResponse):
    """
    This lazy serialization doesn't actually convert our context to JSON
    until the very last minute, using resolve_context.

    That allows things like our autocomplete decorator and other functions
    that peek into the context to behave as normal. They'll be handed
    regular Python objects.
    """

    def __init__(
        self, request: HttpRequest, template: Type[T], *args: Any, **kwargs: Any,
    ) -> None:
        self.template = template
        super().__init__(request, *args, **kwargs)

    def __getstate__(self) -> Any:
        """
        First run the normal pickling of `TemplateResponse`. That already has
        special handling.

        Then, remove our template from pickling because it cannot and should
        not be pickled. The response only cares about the rendered content.
        """
        obj_dict = super().__getstate__()  # type: ignore[misc]
        del obj_dict["template"]
        return obj_dict

    def resolve_context(self, context: Optional[Dict[str, Any]]) -> JSON:
        generated_schema = create_schema(self.template, {})
        return serialize(context, generated_schema)


def template(cls: Type[T]) -> Type[T]:
    from . import type_registry, template_registry

    type_name = f"{cls.__name__}Props"
    type_registry[type_name] = cls  # type: ignore[assignment]
    template_registry[cls.__name__] = type_name  # type: ignore[assignment]

    class Augmented(cls):  # type: ignore[misc, valid-type]
        def items(self) -> Any:
            """
            Duck-typing for context, so you can loop over a template.

            See autocomplete.
            """
            return self._asdict().items()

        def get_serialized(self) -> Any:
            from .serialization import serialize, create_schema

            generated_schema = create_schema(cls, {})
            return serialize(self, generated_schema)

        def render(self, request: HttpRequest) -> TemplateResponse:
            response = LazySerializationResponse(  # type
                request, cls, f"{self.__class__.__name__}.tsx", self,
            )
            return response

    Augmented.__name__ = cls.__name__
    return Augmented


class Action(NamedTuple):
    name: str


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
            context_form_sets = {
                name: possible_form_set
                for name, possible_form_set in context.items()
                if isinstance(possible_form_set, forms.BaseFormSet)
            }
            context_actions = {
                name: possible_action
                for name, possible_action in context.items()
                if isinstance(possible_action, Action)
            }

            return TemplateResponse(
                request,
                "reactivated/interface.html",
                {
                    **self._asdict(),
                    "forms": context_forms,
                    "form_sets": context_form_sets,
                    "actions": context_actions,
                    "serialized": serialized,
                },
            )

        def as_json(self, request: HttpRequest) -> JsonResponse:
            return JsonResponse(self.get_serialized())

    Augmented.__name__ = cls.__name__  # type: ignore[attr-defined]
    return Augmented  # type: ignore[return-value]
