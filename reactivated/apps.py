import atexit
import importlib
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, NamedTuple, Tuple

from django.apps import AppConfig
from django.conf import settings

from . import extract_views_from_urlpatterns, types
from .serialization import create_schema
from .serialization.registry import (
    definitions_registry,
    global_types,
    template_registry,
    type_registry,
    value_registry,
)

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
    reverse: types.URLSchema = {}

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

    context_processors = []

    from .serialization.context_processors import create_context_processor_type

    for engine in settings.TEMPLATES:
        if engine["BACKEND"] == "reactivated.backend.JSX":
            context_processors.extend(engine["OPTIONS"]["context_processors"])  # type: ignore[index]

    type_registry["Context"] = create_context_processor_type(context_processors)

    ParentTuple = NamedTuple("ParentTuple", type_registry.items())  # type: ignore[misc]
    parent_schema, definitions = create_schema(ParentTuple, definitions_registry)
    definitions_registry.update(definitions)

    return {
        "definitions": definitions,
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
    }


def get_templates() -> Dict[str, Tuple[Any]]:
    return template_registry


def get_values() -> Dict[str, Any]:
    return value_registry


def get_schema() -> str:
    schema = {
        "urls": get_urls_schema(),
        "templates": get_templates(),
        "types": get_types_schema(),
        "values": get_values(),
    }
    return json.dumps(schema, indent=4)


class ReactivatedConfig(AppConfig):
    name = "reactivated"

    def ready(self) -> None:
        """
        Django's dev server actually starts twice. So we prevent generation on
        the first start. TODO: handle noreload.
        """

        from .checks import check_installed_app_order  # NOQA
        from .serialization import widgets  # noqa

        if (
            os.environ.get("WERKZEUG_RUN_MAIN") == "true"
            or os.environ.get("RUN_MAIN") == "true"
        ):
            # Triggers for the subprocess of the dev server after restarts or initial start.
            pass

        is_server_started = "DJANGO_SEVER_STARTING" in os.environ

        if is_server_started is False:
            os.environ["DJANGO_SEVER_STARTING"] = "true"
            return

        # TODO: generate this on first request, to avoid running a ton of stuff
        # on tests. Then cache it going forward.
        schema = get_schema()

        generate_schema(schema)
        entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

        client_process = subprocess.Popen(
            [
                "node",
                f"{settings.BASE_DIR}/node_modules/reactivated/build.client.js",
                *entry_points,
            ],
            stdout=subprocess.PIPE,
            env={**os.environ.copy()},
        )
        from reactivated import renderer

        renderer.renderer_process = subprocess.Popen(
            ["node", f"{settings.BASE_DIR}/node_modules/reactivated/build.renderer.js"],
            encoding="utf-8",
            stdout=subprocess.PIPE,
            env={
                **os.environ.copy(),
            },
        )

        def cleanup() -> None:
            # Pytest has issues with this, see https://github.com/pytest-dev/pytest/issues/5502
            # We can't use the env variable PYTEST_CURRENT_TEST because this happens
            # after running all tests and closing the session.
            # See: https://stackoverflow.com/questions/25188119/test-if-code-is-executed-from-within-a-py-test-session
            if "pytest" not in sys.modules:
                logger.info("Cleaning up client build process")
                logger.info("Cleaning up renderer build process")
            client_process.terminate()

            if renderer.renderer_process is not None:
                renderer.renderer_process.terminate()

        atexit.register(cleanup)


def generate_schema(schema: str, skip_cache: bool = False) -> None:
    """
    For development usage only, this requires Node and Python installed

    You can use this function for your E2E test prep.
    """
    logger.info("Generating interfaces and client side code")
    encoded_schema = schema.encode()

    import hashlib

    digest = hashlib.sha1(encoded_schema).hexdigest().encode()

    if skip_cache is False and os.path.exists(
        f"{settings.BASE_DIR}/client/generated/index.tsx"
    ):
        with open(f"{settings.BASE_DIR}/client/generated/index.tsx", "r+b") as existing:
            already_generated = existing.read()

            if digest in already_generated:
                logger.info("Skipping generation as nothing has changed")
                return

    #: Note that we don't pass the file object to stdout, because otherwise
    # webpack gets confused with the half-written file when we make updates.
    # Maybe there's a way to force it to be a single atomic write? I tried
    # open('w+b', buffering=0) but no luck.
    process = subprocess.Popen(
        ["node", f"{settings.BASE_DIR}/node_modules/reactivated/generator.js"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        cwd=settings.BASE_DIR,
    )
    out, error = process.communicate(encoded_schema)

    constants_process = subprocess.Popen(
        [
            "node",
            f"{settings.BASE_DIR}/node_modules/reactivated/generator/constants.js",
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        cwd=settings.BASE_DIR,
    )
    constants_out, constants_error = constants_process.communicate(encoded_schema)

    os.makedirs(f"{settings.BASE_DIR}/client/generated", exist_ok=True)

    with open(f"{settings.BASE_DIR}/client/generated/index.tsx", "w+b") as output:
        output.write(b"// Digest: %s\n" % digest)
        output.write(out)

    with open(f"{settings.BASE_DIR}/client/generated/constants.tsx", "w+b") as output:
        output.write(constants_out)

    logger.info("Finished generating.")
