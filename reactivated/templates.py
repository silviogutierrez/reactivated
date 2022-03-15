from typing import Any, Dict, NamedTuple, Optional, Type, TypeVar

from django import forms
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from . import utils
from .renderer import should_respond_with_json
from .serialization import create_schema, serialize
from .serialization.registry import (
    JSON,
    definitions_registry,
    interface_registry,
    template_registry,
    type_registry,
)

T = TypeVar("T", bound=NamedTuple)


class LazySerializationResponse(TemplateResponse):
    """
    This lazy serialization doesn't actually convert our context to JSON
    until the very last minute, using resolve_context.

    That allows things like our autocomplete decorator and other functions
    that peek into the context to behave as normal. They'll be handed
    regular Python objects.
    """

    _request: HttpRequest

    def __init__(
        self,
        request: HttpRequest,
        template: Type[T],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.template = template
        super().__init__(request, *args, **kwargs)

    @property
    def rendered_content(self) -> str:
        from .backend import JSXTemplate

        engine = utils.get_template_engine()
        template = JSXTemplate(self.template_name, engine)  # type: ignore[arg-type]
        context = self.resolve_context(self.context_data)
        return template.render(context, self._request)

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

        generated_schema = create_schema(self.template, definitions_registry)
        return serialize(context, generated_schema)


def template(cls: Type[T]) -> Type[T]:
    type_name = f"{cls.__name__}Props"

    class Augmented(cls):  # type: ignore[misc, valid-type]
        @staticmethod
        def register() -> None:
            type_registry[type_name] = cls  # type: ignore[assignment]
            template_registry[cls.__name__] = type_name  # type: ignore[assignment]

        def items(self) -> Any:
            """
            Duck-typing for context, so you can loop over a template.

            See autocomplete.
            """
            return self._asdict().items()

        def get_serialized(self) -> Any:
            generated_schema = create_schema(cls, {})
            return serialize(self, generated_schema)

        def render(self, request: HttpRequest) -> TemplateResponse:
            response = LazySerializationResponse(  # type
                request,
                cls,
                f"{self.__class__.__name__}.tsx",
                self,
            )
            return response

    Augmented.register()
    Augmented.__name__ = cls.__name__
    return Augmented


class Action(NamedTuple):
    name: str


class Extracted(NamedTuple):
    context_forms: Dict[str, forms.BaseForm]
    context_form_sets: Dict[str, forms.BaseFormSet]
    context_actions: Dict[str, Action]


def extract_forms_form_sets_and_actions(interface: Any) -> Extracted:
    context = interface._asdict()

    context_forms = {}
    context_form_sets = {}
    context_actions = {}

    for name, item in context.items():
        if isinstance(item, forms.BaseForm):
            context_forms[name] = item

        elif isinstance(item, forms.BaseFormSet):
            context_form_sets[name] = item

        elif isinstance(item, Action):
            context_actions[name] = item
        elif getattr(item, "is_reactivated_interface", None) is True:
            children = extract_forms_form_sets_and_actions(item)
            context_forms.update(children.context_forms)
            context_form_sets.update(children.context_form_sets)
            context_actions.update(children.context_actions)

    return Extracted(
        context_forms=context_forms,
        context_form_sets=context_form_sets,
        context_actions=context_actions,
    )


def interface(cls: Type[T]) -> Type[T]:
    type_name = f"{cls.__name__}Props"

    class Augmented(cls):  # type: ignore[misc, valid-type]
        is_reactivated_interface = True

        @staticmethod
        def register() -> None:
            type_registry[type_name] = cls  # type: ignore[assignment]
            interface_registry[cls.__name__] = type_name  # type: ignore[assignment]

        def get_serialized(self) -> Any:
            generated_schema = create_schema(cls, definitions_registry)
            return serialize(self, generated_schema)

        def render(self, request: HttpRequest) -> HttpResponse:
            import simplejson

            serialized = simplejson.dumps(self.get_serialized(), indent=4)

            if should_respond_with_json(request):
                return HttpResponse(serialized, content_type="application/json")

            extracted_context = extract_forms_form_sets_and_actions(self)

            return TemplateResponse(
                request,
                "reactivated/interface.html",
                {
                    **self._asdict(),
                    "forms": extracted_context.context_forms,
                    "form_sets": extracted_context.context_form_sets,
                    "actions": extracted_context.context_actions,
                    "serialized": serialized,
                },
            )

        def as_json(self, request: HttpRequest) -> JsonResponse:
            return JsonResponse(self.get_serialized())

    Augmented.register()
    Augmented.__name__ = cls.__name__
    return Augmented
