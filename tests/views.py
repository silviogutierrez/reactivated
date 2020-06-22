from typing import Union

from django.http import HttpRequest, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from reactivated.forms import autocomplete
from server.apps.samples import forms  # type: ignore


@autocomplete
def autocomplete_view(
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
    form = forms.OperaForm()
    if request.method == "POST":
        return redirect("/")

    return TemplateResponse(request, "does_not_matter.html", {"form": form})
