from typing import Any

import requests
import simplejson
from django.conf import settings
from django.http import HttpRequest
from django.template.defaultfilters import escape


def render_jsx_to_string(
    request: HttpRequest, template_name: str, context: Any, props: Any
) -> str:
    from reactivated import encode_complex_types

    payload = {"context": {**context, "template_name": template_name}, "props": props}
    data = simplejson.dumps(payload, indent=4, default=encode_complex_types)
    headers = {"Content-Type": "application/json"}

    if "debug" in request.GET:
        return f"<html><body><h1>Debug response</h1><pre>{escape(data)}</pre></body></html>"
    elif "raw" in request.GET or settings.REACTIVATED_SERVER is None:
        request._is_reactivated_response = True  # type: ignore[attr-defined]
        return data

    return requests.post(  # type: ignore[no-any-return]
        f"{settings.REACTIVATED_SERVER}/__ssr/", headers=headers, data=data
    ).json()["rendered"]
