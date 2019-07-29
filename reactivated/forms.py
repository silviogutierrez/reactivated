from .widgets import Autocomplete

from django import forms as django_forms
from django.http import JsonResponse


def autocomplete(view_func):
    def wrapped_view(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        autocomplete = request.GET.get("autocomplete", None)
        query = request.GET.get("query", "")

        if autocomplete is None:
            return response

        for key, item in response.context_data.items():
            if isinstance(item, django_forms.BaseForm):
                form = item
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

    return wrapped_view
