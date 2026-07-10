from reactivated.templates import Template


class HomePage(Template):
    stars: str


class Documentation(Template):
    content: str
    toc: tuple[tuple[str, str], ...]
    path: str
