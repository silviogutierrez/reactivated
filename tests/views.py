from typing import NamedTuple, Union

from django.http import HttpRequest, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from reactivated import template
from reactivated.forms import autocomplete
from sample.server.apps.samples import forms


@autocomplete
def autocomplete_view(
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
    form = forms.OperaForm(request.POST or None)

    if form.is_valid():
        return redirect("/")

    return TemplateResponse(request, "does_not_matter.html", {"form": form})


@autocomplete
def typed_autocomplete_view(
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
    @template
    class DoesNotMatter(NamedTuple):
        form: forms.OperaForm

    if request.method == "POST":
        return redirect("/")

    return DoesNotMatter(form=forms.OperaForm()).render(request)
