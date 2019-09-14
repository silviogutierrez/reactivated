from reactivated import template, Pick
from typing import NamedTuple
from django.http import HttpRequest
from django.template.response import TemplateResponse

from . import models


@template
class TypedTemplate(NamedTuple):
    opera: Pick[models.Opera, "name", "composer.name", "has_piano_transcription"]
    composer: Pick[
        models.Composer,
        "name",
        "countries.name",
        "countries.continent.name",
        "countries.continent.hemisphere",
        "countries.continent.countries.name",
    ]

    def render(self, request: HttpRequest) -> TemplateResponse:
        from reactivated.pick import BasePickHolder, serialize
        from reactivated import utils
        from typing import get_type_hints

        members = get_type_hints(self)

        serialized = {}

        for key, value in self._asdict().items():
            to_be_picked = members.get(key)

            if issubclass(to_be_picked, BasePickHolder):
                serialized[key] = serialize(value, to_be_picked.get_json_schema())
            else:
                serialized[key] = value

        return TemplateResponse(request, f"{self.__class__.__name__}.tsx", serialized)
