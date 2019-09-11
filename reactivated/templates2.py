from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING, Generic, TypeVar, get_type_hints, Any
from mypy_extensions import TypedDict


T = TypeVar("T")
D = TypeVar("D")


class MyModel:
    pass


class Data:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        return cls


class ClassGetItem:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        return cls


Reusable = Data[
    MyModel,
    [
        "field",
        "bar",
        "def",
        "asdasdasd",
        "deasdsadsad",
        "asdadsdasdasdas",
        "abcde",
    ],
    True,
]


Reusable2 = Data[
    MyModel,
    ClassGetItem["true"],
]


class Foo(NamedTuple):
    foo: str
    bar: Data[MyModel, {"field", "bar"}]
    spam: Reusable
    # spam: Reusable
    # bar2: Data2(MyModel, 'abc')


f = Foo(foo="abc", bar=1, spam=2)

hints = get_type_hints(Foo)

print(hints)
