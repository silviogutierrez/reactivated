from typing import Any, List

import requests
import simplejson
from django.conf import settings
from django.http import HttpRequest
from django.template.defaultfilters import escape


def get_accept_list(request: HttpRequest) -> List[str]:
    """
    Given the incoming request, return a tokenized list of media
    type strings.

    From https://github.com/encode/django-rest-framework/blob/master/rest_framework/negotiation.py
    """
    header = request.META.get("HTTP_ACCEPT", "*/*")
    return [token.strip() for token in header.split(",")]


def should_respond_with_json(request: HttpRequest) -> bool:
    accepts = get_accept_list(request)

    return request.GET.get("format", None) == "json" or any(
        ["application/json" in content_type for content_type in accepts]
    )


def render_jsx_to_string(
    request: HttpRequest, template_name: str, context: Any, props: Any
) -> str:
    from reactivated import encode_complex_types

    respond_with_json = should_respond_with_json(request)

    payload = {"context": {**context, "template_name": template_name}, "props": props}
    data = simplejson.dumps(payload, indent=4, default=encode_complex_types)
    headers = {"Content-Type": "application/json"}

    if "debug" in request.GET:
        return f"<html><body><h1>Debug response</h1><pre>{escape(data)}</pre></body></html>"
    elif (
        respond_with_json or "raw" in request.GET or settings.REACTIVATED_SERVER is None
    ):
        request._is_reactivated_response = True  # type: ignore[attr-defined]
        return data

    return requests.post(  # type: ignore[no-any-return]
        f"{settings.REACTIVATED_SERVER}/__ssr/", headers=headers, data=data
    ).json()["rendered"]
