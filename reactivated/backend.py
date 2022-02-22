from typing import Any, Callable, Dict, List, NamedTuple, Optional

from django.conf import settings
from django.http import HttpRequest
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from .renderer import render_jsx_to_string
from .serialization import create_schema, serialize


class JSX(BaseEngine):
    # Name of the subdirectory containing the templates for this engine
    # inside an installed application.
    # app_dirname = 'foobar'

    def __init__(self, params: Any) -> None:
        # params = params.copy()
        options = params.pop("OPTIONS").copy()

        self.context_processors = options.pop("context_processors", [])
        super().__init__(params)

        # self.engine = foobar.Engine(**options)

    def from_string(self, template_code: str) -> Any:
        raise TemplateSyntaxError("Unsupported with JSX")

    def get_template(self, template_name: str) -> "JSXTemplate":  # type: ignore[override]
        adapter = self.template_adapters.get(template_name)

        if adapter is not None:
            return AdapterTemplate(adapter, self)

        raise TemplateDoesNotExist([], backend=self)  # type: ignore[arg-type]

    @cached_property
    def template_adapters(self) -> Dict[str, NamedTuple]:
        adapters = {}

        [
            adapters.update(import_string(path))
            for path in getattr(settings, "REACTIVATED_ADAPTERS", [])
        ]

        return adapters

    @cached_property
    def template_context_processors(self) -> List[Callable[[HttpRequest], Any]]:
        return [import_string(path) for path in self.context_processors]


class JSXTemplate:
    def __init__(self, jsx_template_name: str, backend: JSX) -> None:
        self.jsx_template_name = jsx_template_name
        self.backend = backend

    def render(self, context: Any = None, request: Optional[HttpRequest] = None) -> str:
        template_name = self.jsx_template_name.replace(".tsx", "").replace(".jsx", "")
        from .serialization.context_processors import (
            BaseContext,
            create_context_processor_type,
        )

        props = context or {}
        react_context = BaseContext(template_name=template_name)._asdict()

        if request is not None:
            for context_processor in self.backend.template_context_processors:
                react_context.update(context_processor(request))

            serialized_context = serialize(
                react_context,
                create_schema(
                    create_context_processor_type(self.backend.context_processors), {}
                ),
            )

            return render_jsx_to_string(request, serialized_context, props)

        assert (
            False
        ), "At this time, only templates with the request object can be rendered with reactivated"


class AdapterTemplate(JSXTemplate):
    def __init__(self, adapter: Any, backend: Any) -> None:
        self.adapter = adapter
        super().__init__(f"{self.adapter.__name__}.tsx", backend)

    def render(self, context: Any = None, request: Optional[HttpRequest] = None) -> str:
        to_be_serialized = self.adapter(**context)
        jsx_context = to_be_serialized.get_serialized()
        return super().render(context=jsx_context, request=request)
