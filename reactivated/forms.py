from .widgets import Autocomplete as Autocomplete

from django import forms as django_forms
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.template.response import TemplateResponse

from typing import TypeVar, cast, Any, Union

T = TypeVar('T')

def autocomplete(view_func: T) -> T:
    def wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response: HttpResponse = view_func(request, *args, **kwargs)  # type: ignore
        autocomplete = request.GET.get("autocomplete", None)
        query = request.GET.get("query", "")

        assert isinstance(response, TemplateResponse)

        if autocomplete is None:
            return response

        context_data = response.context_data or {}

        for key, item in context_data.items():
            if isinstance(item, django_forms.BaseForm):
                form: Union[django_forms.BaseForm, None] = item
                break
        else:
            form = None

        if (
            form is not None
            and autocomplete in form.fields
            and isinstance(form.fields[autocomplete], django_forms.ModelChoiceField)
            and isinstance(form.fields[autocomplete].widget, Autocomplete)
        ):
            results = [
                {"value": result.pk, "label": str(result)}
                for result in form.fields[autocomplete].queryset.filter(
                    name__icontains=query
                )[:50]
            ]

            return JsonResponse({"results": results})

        return response

    return cast(T, wrapped_view)
