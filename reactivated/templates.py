from typing import Any, NamedTuple, TypeVar, Union, get_type_hints

from django.http import HttpRequest
from django.template.response import TemplateResponse

from .pick import BasePickHolder
from .stubs import _GenericAlias

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

            members = get_type_hints(self)

            serialized = {}

            for key, value in self._asdict().items():
                to_be_picked = members.get(key)

                assert to_be_picked is not None

                if (
                    isinstance(to_be_picked, _GenericAlias)
                    and to_be_picked.__origin__ is Union
                    and issubclass(to_be_picked.__args__[0], BasePickHolder)
                ):
                    serialized[key] = serialize(
                        value, to_be_picked.__args__[0].get_json_schema()
                    )
                elif isinstance(to_be_picked, _GenericAlias):
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

    Augmented.__name__ = cls.__name__  # type: ignore[attr-defined]
    return Augmented  # type: ignore[return-value]
