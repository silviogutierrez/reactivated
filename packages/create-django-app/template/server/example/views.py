from django.http import (
    HttpRequest,
    HttpResponse,
)

from . import forms, templates
from django.utils.version import get_docs_version


def django_default(request: HttpRequest,) -> HttpResponse:
    form = forms.StoryboardForm()
    return templates.DjangoDefault(form=form, version=get_docs_version()).render(request)
