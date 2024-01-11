from typing import TypedDict

from django.http import HttpRequest
from django.utils.version import get_docs_version


class DjangoVersion(TypedDict):
    django_version: str


def django_version(request: HttpRequest) -> DjangoVersion:
    return {"django_version": get_docs_version()}
