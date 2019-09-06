from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.backends.utils import csrf_token_lazy
from django.template.backends.base import BaseEngine
from django.utils.functional import cached_property
from django.utils.module_loading import import_string


import os

from . import render_jsx_to_string


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
        return "ABC"
        """
        try:
          return Template(self.engine.from_string(template_code))
        except foobar.TemplateCompilationFailed as exc:
            raise TemplateSyntaxError(exc.args)
        """

    def get_template(self, template_name):
        if template_name.endswith(".html"):
            jsx_template_name = template_name.replace(".html", ".tsx")

            if os.path.isfile(
                os.path.join(settings.BASE_DIR, "client/templates", jsx_template_name)
            ):
                return Template(jsx_template_name, self)

        if template_name.endswith(".tsx") or template_name.endswith(".jsx"):
            if os.path.isfile(
                os.path.join(settings.BASE_DIR, "client/templates", template_name)
            ):
                return Template(template_name, self)

        raise TemplateDoesNotExist([], backend=self)

    @cached_property
    def template_context_processors(self):
        return [import_string(path) for path in self.context_processors]


class Template:
    def __init__(self, jsx_template_name, backend):
        self.jsx_template_name = jsx_template_name
        self.backend = backend

    def get_props(self, context=None, request=None):
        if self.jsx_template_name == "registration/login.tsx":
            return {"form": context["form"]}
        elif self.jsx_template_name == "404.tsx":
            return {"request_path": context["request_path"]}
        elif self.jsx_template_name == "flatpages/default.tsx":
            flatpage = context["flatpage"]
            import markdown

            return {
                "flatpage": {
                    "title": flatpage.title,
                    "url": flatpage.url,
                    "content": markdown.markdown(flatpage.content),
                }
            }
        else:
            return context

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
