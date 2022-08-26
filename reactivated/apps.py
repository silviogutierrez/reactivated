import importlib
import json
import logging
import os
import subprocess
from typing import Any, Dict, NamedTuple, Tuple

from django.apps import AppConfig
from django.conf import settings

from . import extract_views_from_urlpatterns, types
from .serialization import create_schema, serialize
from .serialization.registry import (
    definitions_registry,
    global_types,
    interface_registry,
    rpc_registry,
    template_registry,
    type_registry,
    value_registry,
)

logger = logging.getLogger("django.server")

GENERATED_DIRECTORY = f"{settings.BASE_DIR}/node_modules/_reactivated"


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

    if "RPCPermission" not in type_registry:
        type_registry["RPCPermission"] = None  # type: ignore[assignment]

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


def get_interfaces() -> Dict[str, Tuple[Any]]:
    return interface_registry


def get_values() -> Dict[str, Any]:
    serialized = {}

    for key, (value, serialize_as_is) in value_registry.items():
        if serialize_as_is is True:
            serialized[key] = value
        else:
            generated_schema = create_schema(value, {})
            generated_schema.definitions["is_static_context"] = True  # type: ignore[index]
            serialized[key] = serialize(value, generated_schema)
    return serialized


def get_schema() -> str:
    schema = {
        "rpc": rpc_registry,
        "urls": get_urls_schema(),
        "templates": get_templates(),
        "interfaces": get_interfaces(),
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

        def regenerate_schema(*args: Any, **kwargs: Any) -> None:
            schema = get_schema()
            generate_schema(schema)

        # file_changed.connect(regenerate_schema)


def generate_schema(schema: str, skip_cache: bool = False) -> None:
    """
    For development usage only, this requires Node and Python installed

    You can use this function for your E2E test prep.
    """
    logger.info("Generating interfaces and client side code")
    encoded_schema = schema.encode()

    import hashlib

    digest = hashlib.sha1(encoded_schema).hexdigest().encode()

    if skip_cache is False and os.path.exists(f"{GENERATED_DIRECTORY}/index.tsx"):
        with open(f"{GENERATED_DIRECTORY}/index.tsx", "r+b") as existing:
            already_generated = existing.read()

            if digest in already_generated:
                logger.info("Skipping generation as nothing has changed")
                return

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

    constants_process = subprocess.Popen(
        ["npm", "exec", "generate_client_constants"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        cwd=settings.BASE_DIR,
    )
    constants_out, constants_error = constants_process.communicate(encoded_schema)

    os.makedirs(GENERATED_DIRECTORY, exist_ok=True)

    with open(f"{GENERATED_DIRECTORY}/index.tsx", "w+b") as output:
        output.write(b"// Digest: %s\n" % digest)
        output.write(out)

    with open(f"{GENERATED_DIRECTORY}/constants.tsx", "w+b") as output:
        output.write(constants_out)

    logger.info("Finished generating.")
