from reactivated.pick import Pick
from typing import NamedTuple
from django.http import HttpRequest
from django.template.response import TemplateResponse

from . import models


foo: Pick[models.Opera] = "abc"

bar: Pick[models.Opera, "name", "composer"] = models.Opera()

jam: Pick[models.Opera] = 6

spam: Pick[models.Opera] = 5


class TypedTemplateTemplate(NamedTuple):
    opera: Pick[models.Opera]
    composer: Pick[models.Composer]

    def render(self, request: HttpRequest) -> TemplateResponse:
        return TemplateResponse(request, "typed_template.tsx", {})
