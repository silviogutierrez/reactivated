from typing import Mapping, Union, TypeVar

from mypy_extensions import TypedDict


Bar = TypeVar('Bar', str, bool)


Thing = Union[Bar]


def mapping_test(thing: Mapping[str, Thing]) -> bool:
    return True


class Foo(TypedDict):
    foo: str
    other: int


a = Foo(foo="a", other=1)
b: Foo = {"foo": "a", "other": 2}
c: Mapping[str, str] = {"foo": "a"}


a == b == c  # Works


mapping_test(c)  # Works, of course
mapping_test(a)  # Does not work
mapping_test(b)  # Does not work
