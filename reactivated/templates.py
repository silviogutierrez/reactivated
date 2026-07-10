from __future__ import annotations

from typing import Any, ClassVar, Type

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe

from .context import get_context_class, get_context_processors
from .renderer import render_jsx_to_string
from .rpc.core import Pick

template_registry: dict[str, Type[Template]] = {}


class Template(Pick):
    _abstract: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("_abstract", False):
            template_registry[cls.__name__] = cls

    def render_to_string(
        self, request: HttpRequest, entry_point: str | None = None
    ) -> str:
        props = self.model_dump(mode="json")

        context_dict: dict[str, Any] = {"template_name": self.__class__.__name__}
        for processor in get_context_processors():
            context_dict.update(processor(request))

        Context = get_context_class()
        context = Context(**context_dict).model_dump(mode="json")

        return render_jsx_to_string(request, context, props, entry_point=entry_point)

    def render(self, request: HttpRequest, status: int = 200) -> HttpResponse:
        response = HttpResponse(self.render_to_string(request), status=status)

        if getattr(request, "_is_reactivated_response", False) is True:
            response["content-type"] = "application/json"

        return response


class AdminView(Template):
    _abstract: ClassVar[bool] = True
    _entry_point: ClassVar[str] = "django.admin"

    def render_fragment(self, request: HttpRequest) -> str:
        rendered = self.render_to_string(request, entry_point=self._entry_point)
        return mark_safe(f"<div data-reactivated-root>{rendered}</div>")


class AdminChangeView(AdminView):
    _abstract: ClassVar[bool] = True

    def change_view(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,  # type: ignore[type-arg]
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        extra_context = extra_context or {}
        extra_context["reactivated_fragment"] = self.render_fragment(request)
        response = model_admin.changeform_view(
            request, object_id, form_url, extra_context
        )
        if isinstance(response, TemplateResponse):
            response.template_name = "reactivated/admin_change_view.html"
        return response


class AdminListView(AdminView):
    _abstract: ClassVar[bool] = True
