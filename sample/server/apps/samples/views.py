from typing import Union

from django.http import (
    HttpRequest,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt

from reactivated.forms import autocomplete

from . import forms, models, templates


def create_composer(
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
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
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
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
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
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

    return TemplateResponse(
        request,
        "data_browser.tsx",
        {
            "composer_form_set": composer_form_set,
            "composer_form": composer_form,
            "opera_form_set": opera_form_set,
            "opera_form": opera_form,
        },
    )


@autocomplete
def typed_template(
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:

    opera = models.Opera.objects.first()
    composer = models.Composer.objects.first()

    assert opera is not None
    assert composer is not None

    return templates.TypedTemplate(
        opera=opera, composer=composer, all_operas=list(models.Opera.objects.all())
    ).render(request)


@autocomplete
def typed_data_browser(
    request: HttpRequest,
) -> Union[TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:

    return templates.DataBrowser(
        composer_form_set=forms.ComposerFormSet(prefix="composer_form_set"),
        composer_form=forms.ComposerForm(prefix="composer_form"),
        opera_form_set=forms.OperaFormSet(prefix="opera_form_set"),
        opera_form=forms.OperaForm(prefix="opera_form-0"),
    ).render(request)


@csrf_exempt
def ajax_playground(
    request: HttpRequest,
) -> Union[
    JsonResponse, TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
]:

    if request.is_ajax():
        return JsonResponse({"ok": "hello", "bar": "spamp"})

    return templates.AjaxPlayground().render(request)


def form_playground(
    request: HttpRequest,
) -> Union[
    JsonResponse, TemplateResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
]:
    form = forms.PlaygroundForm(request.POST or None)

    return templates.FormPlayground(form=form).render(request)
