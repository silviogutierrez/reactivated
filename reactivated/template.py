from django.conf import settings
from django.middleware.csrf import get_token
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends.base import BaseEngine

import os
import simplejson
import markdown

from . import render_jsx


class JSX(BaseEngine):
    # Name of the subdirectory containing the templates for this engine
    # inside an installed application.
    # app_dirname = 'foobar'

    def __init__(self, params):
        # params = params.copy()
        options = params.pop('OPTIONS').copy()
        super().__init__(params)

        # self.engine = foobar.Engine(**options)

    def from_string(self, template_code):
        return 'ABC'
        """
        try:
          return Template(self.engine.from_string(template_code))
        except foobar.TemplateCompilationFailed as exc:
            raise TemplateSyntaxError(exc.args)
        """

    def get_template(self, template_name):
        if template_name.endswith('.html'):
            jsx_template_name = template_name.replace('.html', '.tsx')

            if os.path.isfile(os.path.join(settings.BASE_DIR, 'client/templates', jsx_template_name)):
                return Template(jsx_template_name)

        raise TemplateDoesNotExist([], backend=self)

        try:
            return Template(self.engine.get_template(template_name))
        except foobar.TemplateNotFound as exc:
            raise TemplateDoesNotExist(exc.args, backend=self)
        except foobar.TemplateCompilationFailed as exc:
            raise TemplateSyntaxError(exc.args)


class Template:
    def __init__(self, jsx_template_name):
        self.jsx_template_name = jsx_template_name

    def get_props(self, context=None, request=None):
        if self.jsx_template_name == 'registration/login.tsx':
            return {
                'form': context['form'],
            }
        elif self.jsx_template_name == '404.tsx':
            return {
                'request_path': context['request_path'],
            }
        elif self.jsx_template_name == 'flatpages/default.tsx':
            flatpage = context['flatpage']

            return {
                'flatpage': {
                    'title': flatpage.title,
                    'url': flatpage.url,
                    'content': markdown.markdown(flatpage.content),
                },
            }
        else:
            assert False


    def render(self, context=None, request=None):
        request._is_jsx_response = True

        props = self.get_props(context, request)
        template_name = self.jsx_template_name.replace('.tsx', '')

        return render_jsx(request, template_name, props)
