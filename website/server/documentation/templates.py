from typing import NamedTuple, Tuple

from reactivated import template


@template
class HomePage(NamedTuple):
    stars: str


@template
class Documentation(NamedTuple):
    content: str
    toc: Tuple[Tuple[str, str], ...]
    path: str
