from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

import pytest
from django.http import HttpRequest, HttpResponse

from reactivated.views import Router


@dataclass
class Area:
    label: str


@dataclass
class Thing:
    pk: int


def _response(body: str) -> HttpResponse:
    return HttpResponse(body.encode())


router = Router()


@router.scope
def stuff(request: HttpRequest) -> Area | HttpResponse:
    if request.META.get("HTTP_X_DENY"):
        return _response("denied")
    return Area(label="root")


@router.scope(parent=stuff)
def thing(area: Area, *, thing_id: int) -> Thing | HttpResponse:
    if thing_id == 404:
        return _response("missing")
    return Thing(pk=thing_id)


@router.index(stuff)
def stuff_list(area: Area, request: HttpRequest) -> HttpResponse:
    return _response(f"list:{area.label}")


@router.view(stuff)
def stuff_check_ins(area: Area, request: HttpRequest) -> HttpResponse:
    return _response("check-ins")


@router.index(thing)
def thing_detail(item: Thing, request: HttpRequest) -> HttpResponse:
    return _response(f"detail:{item.pk}")


@router.view(thing)
def thing_export(item: Thing, area: Area, request: HttpRequest) -> HttpResponse:
    return _response(f"export:{item.pk}:{area.label}")


@router.view(thing_detail)
def thing_notes(item: Thing, request: HttpRequest, *, key: str) -> HttpResponse:
    return _response(f"notes:{item.pk}:{key}")


def test_route_derivation() -> None:
    assert router.routes() == [
        ("stuff/", "stuff_list"),
        ("stuff/check-ins/", "stuff_check_ins"),
        ("stuff/<int:thing_id>/", "thing_detail"),
        ("stuff/<int:thing_id>/export/", "thing_export"),
        ("stuff/<int:thing_id>/notes/<str:key>/", "thing_notes"),
    ]


def test_chain_execution_and_shapes(rf: object) -> None:
    request = rf.get("/")  # type: ignore[attr-defined]

    assert stuff_list(request).content == b"list:root"
    assert thing_detail(request, thing_id=7).content == b"detail:7"
    # 3-arity view receives the root product:
    assert thing_export(request, thing_id=7).content == b"export:7:root"
    # view-parenting: parent's param + own kw param both flow:
    assert thing_notes(request, thing_id=7, key="k").content == b"notes:7:k"


def test_scope_early_return(rf: object) -> None:
    denied = rf.get("/")  # type: ignore[attr-defined]
    denied.META["HTTP_X_DENY"] = "1"
    assert thing_detail(denied, thing_id=7).content == b"denied"

    ok = rf.get("/")  # type: ignore[attr-defined]
    assert thing_detail(ok, thing_id=404).content == b"missing"


def test_paths_are_django_patterns() -> None:
    names = [pattern.name for pattern in router.paths()]
    assert names[0] == "stuff_list"


def test_bad_url_param_annotation() -> None:
    other = Router()
    with pytest.raises(TypeError, match="URL param"):

        @other.scope
        def broken(request: HttpRequest, *, flag: bool) -> Area | HttpResponse:
            raise NotImplementedError


def test_bad_leaf_name() -> None:
    with pytest.raises(TypeError, match="must start with"):

        @router.view(stuff)
        def unrelated_name(area: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_bad_arity() -> None:
    with pytest.raises(TypeError, match="must take"):

        @router.view(stuff)  # type: ignore[arg-type]
        def stuff_broken(area: Area) -> HttpResponse:
            raise NotImplementedError


def test_params_banned_in_path_strings() -> None:
    with pytest.raises(TypeError, match="static words only"):

        @router.view(stuff, path="a/<int:b>")
        def stuff_bad_path(area: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_duplicate_route_rejected() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    @other.index(area)
    def area_list(a: Area, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError

    @other.index(area)
    def area_detail(a: Area, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError

    with pytest.raises(TypeError, match="duplicate route"):
        other.routes()


def test_empty_path_on_view_rejected() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    with pytest.raises(TypeError, match="router.index"):

        @other.view(area, path="")
        def area_home(a: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_index_naming_lint() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    with pytest.raises(TypeError, match="must start with"):

        @other.index(area)
        def unrelated(a: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_pinned_view_name_still_linted() -> None:
    # path= pins the URL; it never relaxes the name.
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    with pytest.raises(TypeError, match="must start with"):

        @other.view(area, path="special")
        def legacy_name(a: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_uuid_param() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    @other.view(area)
    def area_item(a: Area, request: HttpRequest, *, ref: uuid.UUID) -> HttpResponse:
        raise NotImplementedError

    assert other.routes() == [("area/item/<uuid:ref>/", "area_item")]


def test_scope_with_request(rf: object) -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="a")

    @other.scope(parent=area, path="")
    def gated(a: Area, request: HttpRequest) -> Thing | HttpResponse:
        if request.META.get("HTTP_X_DENY"):
            return _response("nope")
        return Thing(pk=1)

    @other.view(gated)
    def gated_page(item: Thing, request: HttpRequest) -> HttpResponse:
        return _response(f"page:{item.pk}")

    assert other.routes() == [("area/page/", "gated_page")]
    ok = rf.get("/")  # type: ignore[attr-defined]
    assert gated_page(ok).content == b"page:1"
    denied = rf.get("/")  # type: ignore[attr-defined]
    denied.META["HTTP_X_DENY"] = "1"
    assert gated_page(denied).content == b"nope"


def test_scope_false_denial(rf: object, settings: object) -> None:
    """False = the canonical denial: a login redirect with next, for
    anonymous and authenticated visitors alike (the Django admin's
    semantics). Also a static check: the False arm must not poison the
    product type — item_page's primary is Thing, and the subtree mypy gate
    verifies that inference."""
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> "Area | HttpResponse | Literal[False]":
        if request.META.get("HTTP_X_DENY"):
            return False
        return Area(label="a")

    @other.scope(parent=area)
    def item(a: Area, *, thing_id: int) -> "Thing | HttpResponse | Literal[False]":
        return Thing(pk=thing_id)

    @other.view(item)
    def item_page(thing: Thing, request: HttpRequest) -> HttpResponse:
        return _response(f"page:{thing.pk}")

    anonymous = rf.get("/protected/")  # type: ignore[attr-defined]
    anonymous.META["HTTP_X_DENY"] = "1"
    response = item_page(anonymous, thing_id=1)
    assert response.status_code == 302
    assert "next=/protected/" in response["Location"]

    class FakeUser:
        is_authenticated = True

    # Authenticated visitors get the same redirect (admin semantics); the
    # login page owns the "authenticated but not authorized" experience.
    authenticated = rf.get("/protected/")  # type: ignore[attr-defined]
    authenticated.META["HTTP_X_DENY"] = "1"
    authenticated.user = FakeUser()
    response = item_page(authenticated, thing_id=1)
    assert response.status_code == 302
    assert "next=/protected/" in response["Location"]

    ok = rf.get("/")  # type: ignore[attr-defined]
    assert item_page(ok, thing_id=7).content == b"page:7"


def test_scope_true_rejected(rf: object) -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> "Area | HttpResponse":
        return True  # type: ignore[return-value]

    @other.index(area)
    def area_list(a: Area, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError

    request = rf.get("/")  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="returned True"):
        area_list(request)
