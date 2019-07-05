from django.apps import AppConfig
from django.conf import settings

import logging
import importlib
import subprocess
import json
import os

from . import extract_views_from_urlpatterns

logger = logging.getLogger("django.server")


def get_types_schema() -> str:
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
            "route": f"/{regex}",
            "args": {
                arg_name: converter_mapping.get(arg_converter.__class__, "string")
                for arg_name, arg_converter in pattern.converters.items()
            },
        }

    return json.dumps(reverse)


class ReactivatedConfig(AppConfig):
    name = "reactivated"

    def ready(self):
        """
        Django's dev server actually starts twice. So we prevent generation on
        the first start. TODO: handle noreload.
        """
        if settings.DEBUG is False:
            return

        is_server_started = "DJANGO_SEVER_STARTING" in os.environ

        if is_server_started is False:
            os.environ["DJANGO_SEVER_STARTING"] = "true"
            return

        logger.info("Generating interfaces and client side code")


        #: Note that we don't pass the file object to stdout, because otherwise
        # webpack gets confused with the half-written file when we make updates.
        # Maybe there's a way to force it to be a single atomic write? I tried
        # open('w+b', buffering=0) but no luck.
        process = subprocess.Popen(
            ["node", "./node_modules/reactivated/generator.js"],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        out, error = process.communicate(get_types_schema().encode())

        with open("client/generated.tsx", "w+b") as output:
            output.write(out)
        logger.info("Finished generating.")
