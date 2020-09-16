import os

from django.conf import settings
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine
from django.template.backends.utils import csrf_token_lazy
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from .renderer import render_jsx_to_string


class JSX(BaseEngine):
    # Name of the subdirectory containing the templates for this engine
    # inside an installed application.
    # app_dirname = 'foobar'

    def __init__(self, params):
        # params = params.copy()
        options = params.pop("OPTIONS").copy()

        self.context_processors = options.pop("context_processors", [])
        super().__init__(params)

        # self.engine = foobar.Engine(**options)

    def from_string(self, template_code):
        raise TemplateSyntaxError("Unsupported with JSX")

    def get_template(self, template_name):
        adapter = self.template_adapters.get(template_name)

        if adapter is not None:
            return AdapterTemplate(adapter, self)

        if template_name.endswith(".tsx") or template_name.endswith(".jsx"):
            if os.path.isfile(
                os.path.join(settings.BASE_DIR, "client/templates", template_name)
            ):
                return JSXTemplate(template_name, self)

        raise TemplateDoesNotExist([], backend=self)

    @cached_property
    def template_adapters(self):
        adapters = {}

        [
            adapters.update(import_string(path))
            for path in getattr(settings, "REACTIVATED_ADAPTERS", [])
        ]

        return adapters

    @cached_property
    def template_context_processors(self):
        return [import_string(path) for path in self.context_processors]


class JSXTemplate:
    def __init__(self, jsx_template_name, backend):
        self.jsx_template_name = jsx_template_name
        self.backend = backend

    def render(self, context=None, request=None):
        template_name = self.jsx_template_name.replace(".tsx", "").replace(".jsx", "")

        props = context or {}
        context = {}

        if request is not None:
            context["request"] = request
            context["csrf_token"] = str(csrf_token_lazy(request))

            for context_processor in self.backend.template_context_processors:
                context.update(context_processor(request))

            return render_jsx_to_string(request, template_name, context, props)

        assert (
            False
        ), "At this time, only templates with the request object can be rendered with reactivated"


class AdapterTemplate(JSXTemplate):
    def __init__(self, adapter, backend):
        self.adapter = adapter
        super().__init__(f"{self.adapter.__name__}.tsx", backend)

    def render(self, context=None, request=None):
        to_be_serialized = self.adapter(**context)
        jsx_context = to_be_serialized.get_serialized()
        return super().render(context=jsx_context, request=request)
