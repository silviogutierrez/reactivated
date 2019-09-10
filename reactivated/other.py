from typing import NamedTuple

from .templates import Template


class TemplateTest(Template):
    thing: str


TemplateTest(thing=2)
