from typing import Union

from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from reactivated.forms import autocomplete

from . import forms, models


def create_composer(
    request: HttpRequest
) -> Union[TemplateResponse, HttpResponseRedirect]:
    if request.method == "POST":
        form = forms.ComposerForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(request.path)
    else:
        form = forms.ComposerForm()

    return TemplateResponse(request, "create_composer.tsx", {"form": form})


def composer_list(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(
        request,
        "composer_list.tsx",
        {"composers": models.Composer.objects.values("pk", "name")},
    )


@autocomplete
def create_opera(
    request: HttpRequest
) -> Union[TemplateResponse, HttpResponseRedirect]:
    if request.method == "POST":
        form = forms.OperaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(request.path)
    else:
        form = forms.OperaForm()

    return TemplateResponse(request, "create_opera.tsx", {"form": form})


@autocomplete
def data_browser(
    request: HttpRequest
) -> Union[TemplateResponse, HttpResponseRedirect]:
    if request.method == "POST":
        form = forms.OperaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(request.path)
    else:
        form = forms.OperaForm()

    composer_form_set = forms.ComposerFormSet(prefix="composer_form_set")
    composer_form = forms.ComposerForm(prefix="composer_form")
    opera_form_set = forms.OperaFormSet(prefix="opera_form_set")
    opera_form = forms.OperaForm(prefix="opera_form-0")

    return TemplateResponse(request, "data_browser.tsx", {
        "composer_form_set": composer_form_set,
        "composer_form": composer_form,
        "opera_form_set": opera_form_set,
        "opera_form": opera_form,
    })