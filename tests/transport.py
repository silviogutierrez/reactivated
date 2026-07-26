from __future__ import annotations

import types
import uuid
from dataclasses import dataclass

import pytest
from django.http import HttpRequest, HttpResponse
from django.urls import path
from django.urls.resolvers import URLPattern

from reactivated.transport import DJANGO_CONVERTERS, mount, url_segment
from reactivated.views import Router


@dataclass
class Area:
    label: str


def _view(request: HttpRequest) -> HttpResponse:
    raise NotImplementedError


class FakeProcedures:
    """A minimal Mountable — the shape any router reduces to."""

    def __init__(self, table: list[tuple[str, str]]) -> None:
        self.table = table

    def routes(self) -> list[tuple[str, str]]:
        return self.table

    def paths(self) -> list[URLPattern]:
        return [path(route, _view, name=name) for route, name in self.table]


def _pages_router() -> Router[HttpRequest]:
    router = Router()

    @router.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    @area.index
    def area_list(a: Area, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError

    return router


def test_url_segment_speaks_django() -> None:
    assert url_segment(int, "pk") == "<int:pk>"
    assert url_segment(str, "slug") == "<str:slug>"
    assert url_segment(uuid.UUID, "ref") == "<uuid:ref>"
    assert set(DJANGO_CONVERTERS) == {int, str, uuid.UUID}


def test_mount_emits_patterns() -> None:
    patterns = mount(_pages_router(), FakeProcedures([("rpc/save_note/", "save_note")]))
    assert [pattern.name for pattern in patterns] == ["area_list", "save_note"]


def test_mount_rejects_duplicate_route_across_routers() -> None:
    with pytest.raises(TypeError, match="duplicate route"):
        mount(
            FakeProcedures([("rpc/save_note/", "save_note")]),
            FakeProcedures([("rpc/save_note/", "other_name")]),
        )


def test_mount_rejects_duplicate_name_across_kinds() -> None:
    # Django's reverse namespace is global: a page and a procedure sharing
    # a name would silently shadow each other without this.
    with pytest.raises(TypeError, match="duplicate reverse name"):
        mount(_pages_router(), FakeProcedures([("rpc/area_list/", "area_list")]))


def test_mount_rejects_non_mountable() -> None:
    with pytest.raises(TypeError, match="not a module or Mountable"):
        mount(object())  # type: ignore[arg-type]


def _module(name: str, router: Router[HttpRequest]) -> types.ModuleType:
    module = types.ModuleType(name)
    module.router = router  # type: ignore[attr-defined]
    return module


def test_mount_accepts_a_module_and_resolves_its_router() -> None:
    # A module is the idiomatic argument: mount takes its `router`. The scope
    # and view in `_pages_router` are defined in THIS module, so the module's
    # name must match for the registration check to pass.
    patterns = mount(_module(__name__, _pages_router()))
    assert [pattern.name for pattern in patterns] == ["area_list"]


def test_mount_dedupes_a_re_exported_router_by_identity() -> None:
    # The shared-tree case: several modules re-export one router. Passing it
    # via each mounts it once, not once-per-module (which would be a duplicate).
    shared = _pages_router()
    patterns = mount(_module(__name__, shared), _module(__name__, shared))
    assert [pattern.name for pattern in patterns] == ["area_list"]


def test_mount_rejects_a_module_that_registered_nothing() -> None:
    # `_pages_router`'s registrations belong to this module, not "unrelated",
    # so mount cannot verify the listed module contributed — a boot error.
    with pytest.raises(TypeError, match="registered no scopes or routes"):
        mount(_module("unrelated", _pages_router()))
