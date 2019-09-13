from typing import NamedTuple, TypeVar


T = TypeVar("T", bound=NamedTuple)


def template(cls: T) -> T:
    from . import type_registry, template_registry
    type_registry[cls.__name__] = cls  # type: ignore
    template_registry[cls.__name__] = {}  # type: ignore

    return cls
