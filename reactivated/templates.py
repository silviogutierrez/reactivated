from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING, Generic, TypeVar
from mypy_extensions import TypedDict

if TYPE_CHECKING:
    from typing import NamedTuple as Template
else:
    from .last import Template


    """
        def __class_getitem__(cls, item): # type: ignore
            return cls
    """


# Bar = TypedDict('Movie', {'name': str, 'year': int})


T = TypeVar('T')
D = TypeVar('D')


class MyModel:
    pass


class Data(Generic[T]):
    pass


class Foo(Template):
    foo: str
    bar: Data[MyModel, {'field'}]
