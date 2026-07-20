from django.http import HttpRequest
from django.urls import URLPattern, URLResolver

from reactivated.rpc import Router

router = Router(HttpRequest)

urlpatterns: list[URLPattern | URLResolver] = []
