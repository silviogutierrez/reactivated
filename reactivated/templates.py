from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING
from mypy_extensions import TypedDict

if TYPE_CHECKING:
    from typing import NamedTuple as Template
else:
    from .last import Template


    """
        def __class_getitem__(cls, item): # type: ignore
            return cls
    """


Bar = TypedDict('Movie', {'name': str, 'year': int})


class Foo(Template):
    foo: str
    bar: Bar


f = Foo(f=1)
