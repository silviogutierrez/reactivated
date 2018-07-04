from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from typing import NamedTuple

import simplejson


class TestTuple(NamedTuple):
    foo: str


def test(request: HttpRequest) -> HttpResponse:
    content = simplejson.dumps(TestTuple(
        foo='thing',
    ))
    return HttpResponse(content, content_type='application/json')
