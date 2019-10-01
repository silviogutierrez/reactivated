from typing import Any, NamedTuple, TypeVar, get_type_hints

from django.http import HttpRequest
from django.template.response import TemplateResponse

from .pick import BasePickHolder, serialize
from .stubs import _GenericAlias

T = TypeVar("T", bound=NamedTuple)


def template(cls: T) -> T:
    from . import type_registry, template_registry

    type_name = f"{cls.__name__}Props"  # type: ignore
    type_registry[type_name] = cls  # type: ignore
    template_registry[cls.__name__] = type_name  # type: ignore

    class Augmented(cls):  # type: ignore
        def get_serialized(self) -> Any:
            members = get_type_hints(self)

            serialized = {}

            for key, value in self._asdict().items():
                to_be_picked = members.get(key)

                assert to_be_picked is not None

                if isinstance(to_be_picked, _GenericAlias):
                    serialized[key] = value
                elif issubclass(to_be_picked, BasePickHolder):
                    serialized[key] = serialize(value, to_be_picked.get_json_schema())
                else:
                    serialized[key] = value
            return serialized

        def render(self, request: HttpRequest) -> TemplateResponse:
            serialized = self.get_serialized()

            return TemplateResponse(
                request, f"{self.__class__.__name__}.tsx", serialized
            )

    Augmented.__name__ = cls.__name__  # type: ignore
    return Augmented  # type: ignore
