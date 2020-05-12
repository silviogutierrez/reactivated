from typing import Optional

import simplejson
from django.http import HttpRequest, JsonResponse
from django.urls import path

from .apps import get_schema
from .utils import get_attribute


def schema(request: HttpRequest, query: Optional[str] = None) -> JsonResponse:
    _schema = simplejson.loads(get_schema())

    if query:
        try:
            _schema = get_attribute(_schema, query.split("/"))
        except KeyError:
            _schema = {"error": "Invalid query"}

    return JsonResponse(_schema)


schema_views = [path("schema/", schema), path("schema/<path:query>/", schema)]
