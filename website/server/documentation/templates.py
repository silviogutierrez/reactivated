from reactivated.pick import Pick
from reactivated.templates import Template


class HomePage(Template):
    stars: str


class TocEntry(Pick):
    href: str
    title: str


class Documentation(Template):
    content: str
    toc: list[TocEntry]
    path: str
