from collections.abc import Callable
from typing import Any  # noqa
from typing import Generic, Literal, TypeVar, Union, overload

from django.db import models

T = TypeVar("T")
S = TypeVar("S", bound=models.Model)
SInstance = TypeVar("SInstance", bound=models.Model)
SOptionalInstance = TypeVar("SOptionalInstance", bound=Union[models.Model, None])
SQuerySet = TypeVar("SQuerySet", bound="models.QuerySet[Any]")
Z = TypeVar("Z", bound=Union["models.QuerySet[Any]", models.Model, None])


class ComputedRelation(Generic[T, S, Z]):
    def __init__(
        self,
        *,
        label: str | None = None,
        fget: Callable[[T], Z],
        model: Callable[[], type[S]] | type[S],
        many: bool,
        null: bool,
    ) -> None:
        self.name = fget.__name__

        self._model = model  # model if isinstance(model, type) else model()
        self.fget: Callable[[T], Z] = fget
        self.many_to_many = many
        self.label = label
        self.null = null

    @property
    def related_model(self) -> type[S]:
        return self._model if isinstance(self._model, type) else self._model()

    @overload
    def __get__(self, instance: None, own: type[T]) -> "ComputedRelation[T, S, Z]":
        pass

    @overload
    def __get__(self, instance: T, own: type[T]) -> Z:
        pass

    def __get__(
        self,
        instance: T | None,
        own: type[T],
    ) -> Union["ComputedRelation[T, S, Z]", Z]:
        if instance is None:
            return self

        return self.fget(instance)


def computed_relation(
    *,
    label: str | None = None,
    model: Callable[[], type[S]] | type[S],
) -> Callable[[Callable[[T], SQuerySet]], ComputedRelation[T, S, SQuerySet]]:
    def inner(fget: Callable[[T], SQuerySet]) -> ComputedRelation[T, S, SQuerySet]:
        return ComputedRelation(
            fget=fget, label=label, model=model, many=True, null=False
        )

    return inner


@overload
def computed_foreign_key(
    *,
    label: str | None = None,
    model: Callable[[], type[S]] | type[S],
    null: Literal[True],
) -> Callable[
    [Callable[[T], SOptionalInstance]], ComputedRelation[T, S, SOptionalInstance]
]: ...


@overload
def computed_foreign_key(
    *,
    label: str | None = None,
    model: Callable[[], type[S]] | type[S],
    null: Literal[False],
) -> Callable[[Callable[[T], SInstance]], ComputedRelation[T, S, SInstance]]: ...


def computed_foreign_key(
    *,
    label: str | None = None,
    model: Callable[[], type[S]] | type[S],
    null: bool = False,
) -> (
    Callable[[Callable[[T], SInstance]], ComputedRelation[T, S, SInstance]]
    | Callable[
        [Callable[[T], SOptionalInstance]], ComputedRelation[T, S, SOptionalInstance]
    ]
):
    def inner(
        fget: Callable[[T], SOptionalInstance]
    ) -> ComputedRelation[T, S, SOptionalInstance]:
        return ComputedRelation(
            fget=fget, label=label, model=model, many=False, null=null
        )

    return inner
