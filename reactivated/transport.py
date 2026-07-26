"""Shared transport vocabulary for the two routers.

Pages (``reactivated.views``) and procedures (``reactivated.rpc``) derive
their URLs from Python signatures. The *grammars* differ — a nested tree of
scopes versus a flat procedure registry — but the vocabulary is one
language: which annotations are URL-convertible, how a param renders as a
Django path segment, and how signature hints resolve. That vocabulary lives
here, once.

``mount()`` is the composition point: every router — page or procedure —
reduces to a ``(route, reverse-name)`` table (the ``Mountable`` protocol),
and Django's reverse namespace is global, so duplicate detection must span
all of them. Per-router checks cannot see a views router and an RPC router
claiming the same name; ``mount()`` can.
"""

import types
import uuid
from typing import Any, Callable, Protocol, get_type_hints, runtime_checkable

from django.urls.resolvers import URLPattern

DJANGO_CONVERTERS: dict[type, str] = {int: "int", str: "str", uuid.UUID: "uuid"}


def resolved_hints(fn: Callable[..., object]) -> dict[str, Any]:
    try:
        return get_type_hints(fn)
    except NameError as error:
        raise TypeError(
            f"transport: cannot resolve annotations for {fn.__qualname__}: {error}"
        ) from error


def url_segment(annotation: type, name: str) -> str:
    return f"<{DJANGO_CONVERTERS[annotation]}:{name}>"


@runtime_checkable
class Mountable(Protocol):
    def routes(self) -> list[tuple[str, str]]:
        """The (route, reverse-name) table this router emits."""
        ...

    def paths(self) -> list[URLPattern]: ...


# Everything urls.py actually wired — schema generation reads THIS, not a
# construction-time global, so an unmounted router can't emit client code.
mounted_routers: list[Mountable] = []


def mount(*items: "Mountable | types.ModuleType") -> list[URLPattern]:
    """Emit every router's patterns with *global* duplicate detection.

    Each argument is either a router or — the idiomatic form — an imported
    module that owns one (``mount(server.crm.annotations, ...)``). A module is
    resolved to its ``router`` attribute and **verified**: it must have
    registered at least one scope or route on that router, so a renamed or
    empty module is a boot error naming it, not a silently missing page. A
    shared-tree module that re-exports the spine's router (``router =
    scopes.router``) is fine — routers dedupe by identity, so passing the same
    one N times mounts it once.

    Routes and reverse names must be unique across everything mounted — pages
    and procedures alike. A conflict is a boot error here, instead of Django
    silently first-matching the route and last-matching the name.
    """
    resolved: dict[int, Mountable] = {}
    for item in items:
        if isinstance(item, types.ModuleType):
            router = getattr(item, "router", None)
            if not isinstance(router, Mountable):
                raise TypeError(
                    f"mount: module {item.__name__!r} has no `router` to mount"
                )
            contributing = getattr(router, "contributing_modules", None)
            if contributing is not None and item.__name__ not in contributing():
                raise TypeError(
                    f"mount: {item.__name__!r} registered no scopes or routes on its "
                    f"router — missing a decorator, or the wrong module?"
                )
            resolved.setdefault(id(router), router)
        elif isinstance(item, Mountable):
            resolved.setdefault(id(item), item)
        else:
            raise TypeError(f"mount: not a module or Mountable: {item!r}")

    routers = list(resolved.values())
    seen_routes: dict[str, str] = {}
    seen_names: dict[str, str] = {}
    patterns: list[URLPattern] = []
    for router in routers:
        for route, name in router.routes():
            if route in seen_routes:
                raise TypeError(
                    f"mount: duplicate route {route!r} ({seen_routes[route]} / {name})"
                )
            if name in seen_names:
                raise TypeError(f"mount: duplicate reverse name {name!r}")
            seen_routes[route] = name
            seen_names[name] = route
        patterns.extend(router.paths())

    # Register only after validation: a rejected router must not linger in
    # the global list where schema generation would still see it.
    for router in routers:
        if router not in mounted_routers:
            mounted_routers.append(router)
    return patterns


__all__ = [
    "DJANGO_CONVERTERS",
    "Mountable",
    "mount",
    "resolved_hints",
    "url_segment",
]
