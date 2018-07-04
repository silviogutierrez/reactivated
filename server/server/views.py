from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from typing import Any, NamedTuple

import simplejson


class JSXResponse(NamedTuple):
    template_name: str
    props: Any


def test(request: HttpRequest) -> HttpResponse:
    content = simplejson.dumps(JSXResponse(
        template_name='DetailView',
        props={
            'thing': 'bar',
        },
    ))
    return HttpResponse(content, content_type='application/json')
