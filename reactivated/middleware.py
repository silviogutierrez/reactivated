from typing import Callable

from django.http import HttpRequest, HttpResponse


class ReactivatedMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if getattr(request, "_is_reactivated_response", False) is True:
            response["content-type"] = "application/json"

        return response
