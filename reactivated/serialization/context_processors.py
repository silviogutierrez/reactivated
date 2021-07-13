from typing import (
    Any,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypedDict,
    get_type_hints,
)

from . import Thing, JSON, create_schema, Intersection
from django.utils.module_loading import import_string

from django.http import HttpRequest


class Message(NamedTuple):
    level: int
    level_tag: Literal["info", "success", "error", "warning", "debug"]
    message: str


class Request(NamedTuple):
    path: str
    url: str

    @classmethod
    def get_serialized_value(
        Type: Type["Request"], value: HttpRequest, schema: Thing
    ) -> JSON:
        return {"path": value.path, "url": value.build_absolute_uri()}


class BaseContext(TypedDict):
    request: Request
    messages: List[Message]
    csrf_token: str
    template_name: str


def create_context_processor_type(context_processors: List[str]) -> Any:
    types = [BaseContext]

    for context_processor in context_processors:
        definition = import_string(context_processor)
        annotations = get_type_hints(definition)
        if annotation := annotations.get("return", None):
            types.append(annotation)

    return Intersection[types]
