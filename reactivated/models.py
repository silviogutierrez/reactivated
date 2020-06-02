from typing import Callable, Generic, Optional, Type, TypeVar, Union, overload

from django.db import models

T = TypeVar("T")
S = TypeVar("S", bound=models.Model)


class ComputedRelation(Generic[T, S]):
    def __init__(
        self,
        *,
        label: Optional[str] = None,
        fget: Callable[[T], "models.QuerySet[S]"],
        model: Type[S],
    ) -> None:
        self.name = fget.__name__
        self.related_model = model
        self.fget: Callable[[T], "models.QuerySet[S]"] = fget
        self.many_to_many = True
        self.label = label

    @overload
    def __get__(self, instance: None, own: Type[T]) -> "ComputedRelation[T, S]":
        pass

    @overload
    def __get__(self, instance: T, own: Type[T]) -> "models.QuerySet[S]":
        pass

    def __get__(
        self, instance: Union[T, None], own: Type[T],
    ) -> Union["ComputedRelation[T, S]", "models.QuerySet[S]"]:
        if instance is None:
            return self

        return self.fget(instance)


def computed_relation(
    *, label: Optional[str] = None, model: Type[S],
) -> Callable[[Callable[[T], "models.QuerySet[S]"]], ComputedRelation[T, S]]:
    def inner(fget: Callable[[T], "models.QuerySet[S]"]) -> ComputedRelation[T, S]:
        return ComputedRelation(fget=fget, label=label, model=model)

    return inner
