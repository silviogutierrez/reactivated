from typing import Mapping, TypeVar, Dict, Any, Callable

from mypy_extensions import TypedDict


Test = Dict[str, str]

T = TypeVar("T", bound=Test)


def mapping_test(thing: T) -> bool:
    return True


class Foo(TypedDict):
    foo: str


class Bar:
    pass


X = TypeVar("X")


def ssr(foo: X) -> X:
    return foo


@ssr
def testing_stuff(b: Bar) -> bool:
    return True


testing_stuff(Bar())
testing_stuff(1)
testing_stuff("atr")
testing_stuff(Test)


a = Foo(foo="a")
b: Foo = {"foo": "a"}
c: Mapping[str, str] = {"foo": "a"}


a == b == c  # Works


# mapping_test(c)  # Works, of course
# mapping_test(a)  # Does not work
