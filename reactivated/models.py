from typing import Any  # noqa
from typing import Callable, Generic, Optional, Type, TypeVar, Union, overload

from django.db import models

T = TypeVar("T")
S = TypeVar("S", bound=models.Model)
SInstance = TypeVar("SInstance", bound=Union[models.Model, None])
SQuerySet = TypeVar("SQuerySet", bound="models.QuerySet[Any]")
Z = TypeVar("Z", bound=Union["models.QuerySet[Any]", models.Model, None])


class ComputedRelation(Generic[T, S, Z]):
    def __init__(
        self,
        *,
        label: Optional[str] = None,
        fget: Callable[[T], Z],
        model: Union[Callable[[], Type[S]], Type[S]],
        many: bool,
    ) -> None:
        self.name = fget.__name__

        self._model = model  # model if isinstance(model, type) else model()
        self.fget: Callable[[T], Z] = fget
        self.many_to_many = many
        self.label = label

    @property
    def related_model(self) -> Type[S]:
        return self._model if isinstance(self._model, type) else self._model()

    @overload
    def __get__(self, instance: None, own: Type[T]) -> "ComputedRelation[T, S, Z]":
        pass

    @overload
    def __get__(self, instance: T, own: Type[T]) -> Z:
        pass

    def __get__(
        self, instance: Union[T, None], own: Type[T],
    ) -> Union["ComputedRelation[T, S, Z]", Z]:
        if instance is None:
            return self

        return self.fget(instance)


def computed_relation(
    *, label: Optional[str] = None, model: Union[Callable[[], Type[S]], Type[S]],
) -> Callable[[Callable[[T], SQuerySet]], ComputedRelation[T, S, SQuerySet]]:
    def inner(fget: Callable[[T], SQuerySet]) -> ComputedRelation[T, S, SQuerySet]:
        return ComputedRelation(fget=fget, label=label, model=model, many=True)

    return inner


def computed_foreign_key(
    *, label: Optional[str] = None, model: Union[Callable[[], Type[S]], Type[S]],
) -> Callable[[Callable[[T], SInstance]], ComputedRelation[T, S, SInstance]]:
    def inner(fget: Callable[[T], SInstance]) -> ComputedRelation[T, S, SInstance]:
        return ComputedRelation(fget=fget, label=label, model=model, many=False)

    return inner
