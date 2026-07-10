import atexit
import os
import signal
import socket
import subprocess
import time
from typing import Any

from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.core.management.commands import runserver
from django.urls import URLPattern, URLResolver

from .generation import GeneratedModule as GeneratedModule
from .generation import generate as generate
from .generation import run_generate_callbacks
from .models import computed_foreign_key as computed_foreign_key  # noqa: F401
from .models import computed_relation as computed_relation  # noqa: F401
from .pick import Pick as Pick  # noqa: F401
from .pick import pick as pick  # noqa: F401
from .templates import Template as Template  # noqa: F401
from .transport import Mountable as Mountable  # noqa: F401
from .transport import mount as mount  # noqa: F401


def terminate_proc(proc: subprocess.Popen[Any]) -> None:
    """
    npm exec doesn't correctly forward signals to its child processes. So,
    simply calling proc.terminate() doesn't actually kill the process. Rather,
    we have to send SIGTERM to the entire process group.
    Note: using this requires that the initial call to subprocess.Popen included
    the `start_new_session=True` flag.
    """
    try:
        pgrp = os.getpgid(proc.pid)
    except ProcessLookupError:
        pass
    else:
        os.killpg(pgrp, signal.SIGTERM)
        proc.communicate(timeout=5)


original_run = runserver.Command.run


def run_generations(skip_cache: bool = False) -> None:
    if "REACTIVATED_SKIP_GENERATIONS" in os.environ:
        return

    # Registries (picks, templates, rpc) fill as modules import; load the
    # url tree first so every views/templates module has registered before
    # any schema is emitted.
    import importlib

    importlib.import_module(settings.ROOT_URLCONF)

    run_generate_callbacks(str(settings.BASE_DIR), skip_cache)

    from .rpc.core import generate_client_schema, generate_server_schema

    generate_server_schema(skip_cache=skip_cache)
    generate_client_schema(skip_cache=skip_cache)

    from .apps import generate_schema

    generate_schema(skip_cache)

    from .generation import prune_orphans

    prune_orphans(str(settings.BASE_DIR))


def get_free_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    free_port = sock.getsockname()[1]
    return free_port  # type: ignore[no-any-return]


def outer_process(cmd: Any) -> None:
    if os.environ.get("REACTIVATED_RENDERER") is not None:
        os.environ["REACTIVATED_SKIP_SERVER"] = "true"
        return

    free_port = get_free_port()
    original_port = cmd.port

    # Lie to the terminal when logging the port we bound to, so the user still
    # visits the original port.
    class LyingPort(int):
        def __str__(self) -> str:
            return str(original_port)

    cmd.port = LyingPort(free_port)

    os.environ["REACTIVATED_VITE_PORT"] = original_port
    os.environ["REACTIVATED_DJANGO_PORT"] = str(free_port)

    run_generations()

    vite_process = subprocess.Popen(
        ["npm", "exec", "start_vite"],
        # stdout=subprocess.PIPE,
        env={**os.environ.copy(), "BASE": f"{settings.STATIC_URL}dist/"},
        start_new_session=True,
    )
    atexit.register(lambda: terminate_proc(vite_process))
    # npm exec is weird and seems to run into duplicate issues if executed
    # too quickly. There are better ways to do this, I assume.
    time.sleep(0.5)

    tsc_process = subprocess.Popen(
        [
            "npm",
            "exec",
            "tsc",
            "--",
            "--watch",
            "--noEmit",
            "--preserveWatchOutput",
        ],
        # stdout=subprocess.PIPE,
        env={**os.environ.copy()},
        start_new_session=True,
    )
    atexit.register(lambda: terminate_proc(tsc_process))

    os.environ["REACTIVATED_RENDERER"] = f"http://localhost:{cmd.port}"


def inner_process(cmd: Any) -> None:
    # Inner process still needs this rebound for Django's built in runserver
    # though maybe not for django_extensions runserver_plus
    free_port = os.environ["REACTIVATED_DJANGO_PORT"]
    original_port = os.environ["REACTIVATED_VITE_PORT"]

    class LyingPort(int):
        def __str__(self) -> str:
            return str(original_port)

    cmd.port = LyingPort(free_port)

    run_generations()


def patched_run(self: Any, **options: Any) -> Any:
    if (os.environ.get("RUN_MAIN") == "true") and os.environ.get(
        "REACTIVATED_SKIP_SERVER"
    ) != "true":
        original_on_bind = runserver.Command.on_bind

        def on_bind(self: Any, server_port: Any) -> None:
            original_on_bind(self, int(os.environ["REACTIVATED_VITE_PORT"]))

        runserver.Command.on_bind = on_bind  # type: ignore[method-assign]

        inner_process(self)
    else:
        outer_process(self)

    return original_run(self, **options)


runserver.Command.run = patched_run  # type: ignore[method-assign]

# Mypy tests have problems with this executing outside a Django context so
# we skip the patching on those runs.
if "MYPY_CONFIG_FILE_DIR" not in os.environ:
    try:
        from django_extensions.management.commands import (  # type: ignore[import-untyped]
            runserver_plus,
        )

        original_run_plus = runserver_plus.Command.inner_run
    except ImportError:
        pass
    else:

        def patched_run_plus(self: Any, options: Any) -> Any:
            if (os.environ.get("WERKZEUG_RUN_MAIN") == "true") and os.environ.get(
                "REACTIVATED_SKIP_SERVER"
            ) != "true":
                inner_process(self)
            else:
                outer_process(self)

            return original_run_plus(self, options)

        runserver_plus.Command.inner_run = patched_run_plus


def describe_pattern(p):  # type: ignore[no-untyped-def]
    return str(p.pattern)


def extract_views_from_urlpatterns(  # type: ignore[no-untyped-def]
    urlpatterns, base="", namespace=None
):
    """
    Heavily modified version of the functiuon from django_extensions/management/commands/show_urls.py

    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a three-tuple: (view_func, regex, name, pattern)
    """
    views = []
    for p in urlpatterns:
        if isinstance(p, URLPattern):
            try:
                name: str | None
                if not p.name:
                    name = p.name
                elif namespace:
                    name = f"{namespace}:{p.name}"
                else:
                    name = p.name
                pattern = describe_pattern(p)  # type: ignore[no-untyped-call]
                views.append((p.callback, base + pattern, name, p.pattern))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, URLResolver):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            if namespace and p.namespace:
                _namespace = f"{namespace}:{p.namespace}"
            else:
                _namespace = p.namespace or namespace
            pattern = describe_pattern(p)  # type: ignore[no-untyped-call]

            if _namespace in getattr(
                settings, "REACTIVATED_IGNORED_URL_NAMESPACES", ["admin"]
            ):
                continue

            views.extend(
                extract_views_from_urlpatterns(  # type: ignore[no-untyped-call]
                    patterns, base + pattern, namespace=_namespace
                )
            )
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)
    return views
