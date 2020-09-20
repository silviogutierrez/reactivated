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

    browser = templates.DataBrowser(
        composer_form_set=forms.ComposerFormSet(
            request.POST or None, prefix="composer_form_set"
        ),
        composer_form=forms.ComposerForm(request.POST or None, prefix="composer_form"),
        opera_form_set=forms.OperaFormSet(
            request.POST or None, prefix="opera_form_set"
        ),
        opera_form=forms.OperaForm(request.POST or None, prefix="opera_form"),
    )

    from django.forms import BaseForm, BaseFormSet

    validated = []

    for form_or_form_set in browser:
        # This is hacky, but essentially, it says: if a form was not touched, treat it as valid if it's bound.
        # If it's touched and bound, then validate it as normal
        # If it's unbound to begin with, then it's not valid.
        # We then modify .is_bound to fool Django into not producing .errors
        # for our form when serialiazing, even though it's bound (but "valid" due to being untouched)
        if isinstance(form_or_form_set, BaseForm):
            validated.append(
                form_or_form_set.is_bound
                and (
                    form_or_form_set.has_changed() is False
                    or form_or_form_set.is_valid()
                )
            )
            form_or_form_set.is_bound = (
                form_or_form_set.is_bound and form_or_form_set.has_changed()
            )
        elif isinstance(form_or_form_set, BaseFormSet):
            validated.append(form_or_form_set.is_valid())  # type: ignore[no-untyped-call]

    if all(validated):
        # Because of the above hack, we still need to test the form was valid.
        # A better design would be to have a dict of all the forms, and the
        # invalid ones are just missing entirely.
        if browser.composer_form.is_valid():
            browser.composer_form.save()

        if browser.opera_form.is_valid():
            browser.opera_form.save()

        browser.composer_form_set.save()
        browser.opera_form_set.save()

        return redirect(request.path)

    return browser.render(request)


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
