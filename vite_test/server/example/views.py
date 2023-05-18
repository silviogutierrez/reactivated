from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.version import get_docs_version

from . import forms, models, templates


def home_page(request: HttpRequest) -> HttpResponse:
    return templates.HomePage().render(request)
