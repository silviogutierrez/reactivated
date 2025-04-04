from typing import NamedTuple

from reactivated import template


@template
class HomePage(NamedTuple):
    stars: str


@template
class Documentation(NamedTuple):
    content: str
    toc: tuple[tuple[str, str], ...]
    path: str
