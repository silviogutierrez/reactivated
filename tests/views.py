from typing import Union

from django.http import HttpRequest, HttpResponseRedirect
from django.template.response import TemplateResponse

from reactivated.forms import autocomplete
from server.apps.samples import forms


@autocomplete
def autocomplete_view(
    request: HttpRequest
) -> Union[TemplateResponse, HttpResponseRedirect]:
    form = forms.OperaForm()

    return TemplateResponse(request, "does_not_matter.html", {"form": form})
