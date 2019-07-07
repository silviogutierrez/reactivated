from typing import Mapping, TypeVar, Dict

from mypy_extensions import TypedDict


Test = Dict[str, str]

T = TypeVar("T", bound=Test)


def mapping_test(thing: T) -> bool:
    return True


class Foo(TypedDict):
    foo: str


class Bar:
    pass


# @ssr
def testing_stuff(b: Bar) -> bool:
    return True


testing_stuff(Bar())  # All of these pass because Bar is "re-typed"
testing_stuff(1)
testing_stuff("atr")
testing_stuff(Test)  # Fails of course


a = Foo(foo="a")
b: Foo = {"foo": "a"}
c: Mapping[str, str] = {"foo": "a"}


a == b == c  # Works


# mapping_test(c)  # Works, of course
# mapping_test(a)  # Does not work


X = TypeVar("X")


def ssr(foo: X) -> X:
    return foo


@ssr
def to_be_ssred_without_types(thing, bar):
    return True


@ssr
def to_be_ssred(thing: int, bar: str) -> bool:
    return True


reveal_type(to_be_ssred)
reveal_type(to_be_ssred_without_types)
