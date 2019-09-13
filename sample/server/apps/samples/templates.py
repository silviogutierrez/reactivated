from reactivated import template, Pick
from typing import NamedTuple
from django.http import HttpRequest
from django.template.response import TemplateResponse

from . import models


@template
class TypedTemplateTemplate(NamedTuple):
    opera: Pick[models.Opera, "name", "composer", "has_piano_transcription"]
    composer: Pick[models.Composer, "name"]

    def render(self, request: HttpRequest) -> TemplateResponse:
        from reactivated.pick import BasePickHolder
        from typing import get_type_hints
        members = get_type_hints(self)

        serialized = {}

        for key, value in self._asdict().items():
            to_be_picked = members.get(key)

            if issubclass(to_be_picked, BasePickHolder):
                instance_fields = {}

                for field in to_be_picked.fields:
                    instance_fields[field] = str(getattr(value, field))
                serialized[key] = instance_fields
            else:
                serialized[key] = value

        return TemplateResponse(request, "typed_template.tsx", serialized)
