import importlib
import json
import logging
import os
import subprocess
from typing import Any, Dict, NamedTuple, Tuple

from django.apps import AppConfig
from django.conf import settings

from . import (
    extract_views_from_urlpatterns,
    global_types,
    template_registry,
    type_registry,
)
from .serialization import create_schema

logger = logging.getLogger("django.server")


def get_urls_schema() -> Dict[str, Any]:
    urlconf = importlib.import_module(settings.ROOT_URLCONF)
    urlpatterns = urlconf.urlpatterns  # type: ignore[attr-defined]

    from django.urls import converters
    from django.urls.resolvers import RoutePattern

    converter_mapping = {
        converters.IntConverter: "number",
        converters.StringConverter: "string",
        converters.UUIDConverter: "string",
        converters.SlugConverter: "string",
        converters.PathConverter: "string",
    }

    urls = extract_views_from_urlpatterns(urlpatterns)  # type: ignore[no-untyped-call]
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

    return reverse


def get_types_schema() -> Any:
    """ The package json-schema-to-typescript does expose a way to
    automatically export any interface it sees. However, this can bloat our
    generated files.

    Instead, while creating the schema, we occasionally run into types that we
    want available globally but are not directly referenced by templates.

    These aren't exported by `json-schem-to-typescript` because they're
    referenced using `tsType`, so the libraary is unaware of their usage.

    So we register them in `globals` and force `json-schema-to-typescript` to
    expose them.

    We can't just add these types to the `type_registry` because that's only
    parsed once when generating the parent tuple.

    We could explore doing two passes in the future.

    See `unreachableDefinitions` in json-schema-to-typescript
    """
    type_registry["globals"] = Any  # type: ignore[assignment]
    ParentTuple = NamedTuple("ParentTuple", type_registry.items())  # type: ignore[misc]
    parent_schema = create_schema(ParentTuple, {})

    return {
        "definitions": parent_schema.definitions,
        **{
            **parent_schema.definitions["reactivated.apps.ParentTuple"],
            "properties": {
                **parent_schema.definitions["reactivated.apps.ParentTuple"][
                    "properties"
                ],
                "globals": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(global_types.keys()),
                    "properties": global_types,
                },
            },
        },
    }


def get_templates() -> Dict[str, Tuple[Any]]:
    return template_registry


def get_schema() -> str:
    schema = {
        "urls": get_urls_schema(),
        "templates": get_templates(),
        "types": get_types_schema(),
    }
    return json.dumps(schema, indent=4)


class ReactivatedConfig(AppConfig):
    name = "reactivated"

    def ready(self) -> None:
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

        generate_schema()


def generate_schema() -> None:
    """
    For development usage only, this requires Node and Python installed

    You can use this function for your E2E test prep.
    """
    logger.info("Generating interfaces and client side code")
    schema = get_schema().encode()

    import hashlib

    digest = hashlib.sha1(schema).hexdigest().encode()

    if os.path.exists("client/generated.tsx"):
        with open("client/generated.tsx", "r+b") as existing:
            already_generated = existing.read()

            if digest in already_generated:
                logger.info("Skipping generation as nothing has changed")
                return

    #: Note that we don't pass the file object to stdout, because otherwise
    # webpack gets confused with the half-written file when we make updates.
    # Maybe there's a way to force it to be a single atomic write? I tried
    # open('w+b', buffering=0) but no luck.
    process = subprocess.Popen(
        ["node", "./node_modules/reactivated/generator.js"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    out, error = process.communicate(schema)

    with open("client/generated.tsx", "w+b") as output:
        output.write(b"// Digest: %s\n" % digest)
        output.write(out)
        logger.info("Finished generating.")
