import importlib
import json
import logging
import os
import pathlib
import subprocess
from typing import Any, NamedTuple

from django.apps import AppConfig
from django.conf import settings

from . import extract_views_from_urlpatterns, types
from .forms.schema import create_schema
from .registry import (
    definitions_registry,
    global_types,
    type_registry,
)

logger = logging.getLogger("django.server")

GENERATED_DIRECTORY = f"{settings.BASE_DIR}/client/generated"


def get_urls_schema() -> dict[str, Any]:
    urlconf = importlib.import_module(settings.ROOT_URLCONF)
    urlpatterns = urlconf.urlpatterns

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
    reverse: types.URLSchema = {}

    for _, regex, name, pattern in urls:
        if not isinstance(pattern, RoutePattern):
            continue
        if not name:
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
    """The package json-schema-to-typescript does expose a way to
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

    from .context import get_context_class

    type_registry["Context"] = get_context_class()  # type: ignore[assignment]

    if "RPCPermission" not in type_registry:
        type_registry["RPCPermission"] = None  # type: ignore[assignment]

    ParentTuple = NamedTuple("ParentTuple", type_registry.items())  # type: ignore[misc]
    parent_schema, definitions = create_schema(ParentTuple, definitions_registry)
    definitions_registry.update(definitions)

    return {
        "$defs": definitions,
        **{
            **definitions["reactivated.apps.ParentTuple"],
            "properties": {
                **definitions["reactivated.apps.ParentTuple"]["properties"],
                "globals": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(global_types.keys()),
                    "properties": global_types,
                },
            },
        },
        "title": "_Types",
    }


def get_templates() -> dict[str, tuple[Any]]:
    # The legacy template registry is gone; rpc templates generate through
    # the client schema instead. The key stays for the generator contract.
    return {}


def get_interfaces() -> dict[str, tuple[Any]]:
    return {}


def get_schema() -> str:
    schema = {
        "rpc": {},
        "urls": get_urls_schema(),
        "templates": get_templates(),
        "interfaces": get_interfaces(),
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

        # Connect signal handlers for migration detection
        from django.db.models.signals import post_migrate, pre_migrate

        from .checks import check_installed_app_order  # NOQA
        from .fields import clear_migrating_flag, set_migrating_flag
        from .forms import widgets  # noqa

        pre_migrate.connect(set_migrating_flag)
        post_migrate.connect(clear_migrating_flag)


def generate_schema(skip_cache: bool = False) -> None:
    schema = get_schema()

    """
    For development usage only, this requires Node and Python installed

    You can use this function for your E2E test prep.
    """
    encoded_schema = schema.encode()

    import hashlib

    digest = hashlib.sha1(encoded_schema).hexdigest().encode()

    from .generation import expect

    expect(pathlib.Path(GENERATED_DIRECTORY) / "index.tsx")

    if skip_cache is False and os.path.exists(f"{GENERATED_DIRECTORY}/index.tsx"):
        with open(f"{GENERATED_DIRECTORY}/index.tsx", "r+b") as existing:
            already_generated = existing.read()

            if digest in already_generated:
                return
    logger.info("Generating interfaces and client side code")

    #: Note that we don't pass the file object to stdout, because otherwise
    # webpack gets confused with the half-written file when we make updates.
    # Maybe there's a way to force it to be a single atomic write? I tried
    # open('w+b', buffering=0) but no luck.
    process = subprocess.Popen(
        ["npm", "exec", "generate_client_assets"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        cwd=settings.BASE_DIR,
    )
    out, error = process.communicate(encoded_schema)

    os.makedirs(GENERATED_DIRECTORY, exist_ok=True)

    from .generation import write_atomic

    index = b"// Digest: %s\n" % digest + out + b'\nexport * from "./schema";\n'
    write_atomic(pathlib.Path(GENERATED_DIRECTORY) / "index.tsx", index.decode("utf-8"))

    logger.info("Finished generating.")
