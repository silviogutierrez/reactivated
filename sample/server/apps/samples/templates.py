from reactivated.pick import Pick
from typing import NamedTuple
from django.http import HttpRequest
from django.template.response import TemplateResponse

from . import models


foo: Pick[models.Opera, "a", "b"] = "abc"

bar: Pick[models.Opera, "name", "composer"] = models.Opera()

jam: Pick[models.Opera, "c", "d"] = 6

spam: Pick[models.Opera, "e", "f"] = 5


class TypedTemplateTemplate(NamedTuple):
    opera: Pick[models.Opera, "name", "composer"]
    composer: Pick[models.Composer, "name"]

    def render(self, request: HttpRequest) -> TemplateResponse:
        from reactivated.pick import Pick, BasePickHolder
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
