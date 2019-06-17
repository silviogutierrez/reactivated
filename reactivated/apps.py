from django.apps import AppConfig
from django.conf import settings

import importlib
import subprocess
import json

from . import extract_views_from_urlpatterns


class ReactivatedConfig(AppConfig):
    name = 'reactivated'

    def ready(self):
        urlconf = importlib.import_module(settings.ROOT_URLCONF)
        urlpatterns = urlconf.urlpatterns

        from server.urls import urlpatterns
        from django_extensions.management.commands.show_urls import Command
        from django.contrib.admindocs.views import simplify_regex
        from django.urls import converters
        from django.urls.resolvers import RoutePattern
        import json

        converter_mapping = {
            converters.IntConverter: "number",
            converters.StringConverter: "string",
            converters.UUIDConverter: "string",
            converters.SlugConverter: "string",
            converters.PathConverter: "string",
        }

        urls = extract_views_from_urlpatterns(urlpatterns)
        reverse = {}

        for _, regex, name, pattern in urls:
            if not isinstance(pattern, RoutePattern):
                continue
            reverse[name or regex] = {
                'route': pattern._route,
                'args': {
                    arg_name: converter_mapping.get(arg_converter.__class__, "string")
                    for arg_name, arg_converter in pattern.converters.items()
                },
            }

        # process = subprocess.Popen(["./node_modules/.bin/ts-node", "./server/renderer.tsx"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)

        with open('client/generated.tsx', 'w') as output:
            process = subprocess.Popen(["node", "./node_modules/reactivated/generator.js"], stdout=output, stdin=subprocess.PIPE)
            out, error = process.communicate(json.dumps(reverse).encode())
