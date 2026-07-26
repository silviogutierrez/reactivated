from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import ClassVar, Literal, assert_type

import pytest
from django.http import HttpRequest, HttpResponse

from reactivated.templates import Template
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


@stuff.scope
def thing(area: Area, *, thing_id: int) -> Thing | HttpResponse:
    if thing_id == 404:
        return _response("missing")
    return Thing(pk=thing_id)


@stuff.index
def stuff_list(area: Area, request: HttpRequest) -> HttpResponse:
    return _response(f"list:{area.label}")


@stuff.view
def stuff_check_ins(area: Area, request: HttpRequest) -> HttpResponse:
    return _response("check-ins")


@thing.index
def thing_detail(item: Thing, request: HttpRequest) -> HttpResponse:
    return _response(f"detail:{item.pk}")


@thing.view
def thing_export(item: Thing, area: Area, request: HttpRequest) -> HttpResponse:
    return _response(f"export:{item.pk}:{area.label}")


@thing.view
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

    assert router.endpoint(stuff_list)(request).content == b"list:root"
    assert router.endpoint(thing_detail)(request, thing_id=7).content == b"detail:7"
    # 3-arity view receives the root product:
    assert (
        router.endpoint(thing_export)(request, thing_id=7).content == b"export:7:root"
    )
    # view-parenting: parent's param + own kw param both flow:
    assert (
        router.endpoint(thing_notes)(request, thing_id=7, key="k").content
        == b"notes:7:k"
    )

    # The decorated name is the ORIGINAL function — direct calls are just
    # calls, fully typed, like RPC handlers:
    assert thing_detail(Thing(pk=9), request).content == b"detail:9"
    assert thing_export(Thing(pk=9), Area(label="x"), request).content == b"export:9:x"


def test_scope_early_return(rf: object) -> None:
    denied = rf.get("/")  # type: ignore[attr-defined]
    denied.META["HTTP_X_DENY"] = "1"
    assert router.endpoint(thing_detail)(denied, thing_id=7).content == b"denied"

    ok = rf.get("/")  # type: ignore[attr-defined]
    assert router.endpoint(thing_detail)(ok, thing_id=404).content == b"missing"


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

        @stuff.view
        def unrelated_name(area: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_bad_arity() -> None:
    with pytest.raises(TypeError, match="must take"):

        @stuff.view  # type: ignore[arg-type]
        def stuff_broken(area: Area) -> HttpResponse:
            raise NotImplementedError


def test_params_banned_in_path_strings() -> None:
    with pytest.raises(TypeError, match="static words only"):

        @stuff.view(path="a/<int:b>")
        def stuff_bad_path(area: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_duplicate_route_rejected() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    @area.index
    def area_list(a: Area, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError

    @area.index
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

        @area.view(path="")
        def area_home(a: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_worded_param_scope(rf: object) -> None:
    # path= pins words on a param scope: one edge carries the word, the
    # param, and the resolution (truth/<uuid> needs no pass-through).
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="a")

    @area.scope(path="truth")
    def truth_item(a: Area, *, thing_id: int) -> Thing | HttpResponse:
        return Thing(pk=thing_id)

    @truth_item.index
    def truth_item_page(item: Thing, request: HttpRequest) -> HttpResponse:
        return _response(f"truth:{item.pk}")

    assert other.routes() == [("area/truth/<int:thing_id>/", "truth_item_page")]
    request = rf.get("/")  # type: ignore[attr-defined]
    assert other.endpoint(truth_item_page)(request, thing_id=4).content == b"truth:4"


def test_child_scope_registers_on_parents_router(rf: object) -> None:
    # The fractal form carries the router through the tree: a chain built
    # entirely off the root scope lands its views on the root's router.
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="a")

    @area.scope
    def item(a: Area, *, thing_id: int) -> Thing | HttpResponse:
        return Thing(pk=thing_id)

    @item.index
    def item_detail(thing: Thing, request: HttpRequest) -> HttpResponse:
        return _response(f"detail:{thing.pk}")

    assert other.routes() == [("area/<int:thing_id>/", "item_detail")]
    request = rf.get("/")  # type: ignore[attr-defined]
    assert other.endpoint(item_detail)(request, thing_id=3).content == b"detail:3"


def test_index_naming_lint() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    with pytest.raises(TypeError, match="must start with"):

        @area.index
        def unrelated(a: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_pinned_view_name_still_linted() -> None:
    # path= pins the URL; it never relaxes the name.
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    with pytest.raises(TypeError, match="must start with"):

        @area.view(path="special")
        def legacy_name(a: Area, request: HttpRequest) -> HttpResponse:
            raise NotImplementedError


def test_uuid_param() -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        raise NotImplementedError

    @area.view
    def area_item(a: Area, request: HttpRequest, *, ref: uuid.UUID) -> HttpResponse:
        raise NotImplementedError

    assert other.routes() == [("area/item/<uuid:ref>/", "area_item")]


def test_scope_with_request(rf: object) -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="a")

    @area.scope(path="")
    def gated(a: Area, request: HttpRequest) -> Thing | HttpResponse:
        if request.META.get("HTTP_X_DENY"):
            return _response("nope")
        return Thing(pk=1)

    @gated.view
    def gated_page(item: Thing, request: HttpRequest) -> HttpResponse:
        return _response(f"page:{item.pk}")

    assert other.routes() == [("area/page/", "gated_page")]
    ok = rf.get("/")  # type: ignore[attr-defined]
    assert other.endpoint(gated_page)(ok).content == b"page:1"
    denied = rf.get("/")  # type: ignore[attr-defined]
    denied.META["HTTP_X_DENY"] = "1"
    assert other.endpoint(gated_page)(denied).content == b"nope"


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

    @area.scope
    def item(a: Area, *, thing_id: int) -> "Thing | HttpResponse | Literal[False]":
        return Thing(pk=thing_id)

    @item.view
    def item_page(thing: Thing, request: HttpRequest) -> HttpResponse:
        return _response(f"page:{thing.pk}")

    anonymous = rf.get("/protected/")  # type: ignore[attr-defined]
    anonymous.META["HTTP_X_DENY"] = "1"
    response = other.endpoint(item_page)(anonymous, thing_id=1)
    assert response.status_code == 302
    assert "next=/protected/" in response["Location"]

    class FakeUser:
        is_authenticated = True

    # Authenticated visitors get the same redirect (admin semantics); the
    # login page owns the "authenticated but not authorized" experience.
    authenticated = rf.get("/protected/")  # type: ignore[attr-defined]
    authenticated.META["HTTP_X_DENY"] = "1"
    authenticated.user = FakeUser()
    response = other.endpoint(item_page)(authenticated, thing_id=1)
    assert response.status_code == 302
    assert "next=/protected/" in response["Location"]

    ok = rf.get("/")  # type: ignore[attr-defined]
    assert other.endpoint(item_page)(ok, thing_id=7).content == b"page:7"


def test_scope_true_rejected(rf: object) -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> "Area | HttpResponse":
        return True  # type: ignore[return-value]

    @area.index
    def area_list(a: Area, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError

    request = rf.get("/")  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="returned True"):
        other.endpoint(area_list)(request)


class FakePage(Template):
    """A real rpc.Template — the binder is nominally coupled to it. The
    render_to_string override keeps the node renderer out of unit tests;
    _abstract keeps it out of template_registry, so the sample app's
    schema generation (same process, e2e) doesn't emit a phantom
    templates.FakePage import."""

    _abstract: ClassVar[bool] = True

    label: str

    def render_to_string(
        self, request: HttpRequest, entry_point: str | None = None
    ) -> str:
        return f"rendered:{self.label}"


def test_template_returns(rf: object) -> None:
    """Views may return a Template (anything with .render); the binder
    renders it. PRG spells as ``FakePage | HttpResponse``. Direct calls
    still get the typed object's response; unit tests can call .fn and
    assert on props without any response parsing."""
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="a")

    @area.view
    def area_page(a: Area, request: HttpRequest) -> FakePage | HttpResponse:
        if request.META.get("HTTP_X_REDIRECT"):
            return _response("went-elsewhere")
        return FakePage(label=a.label)

    ok = rf.get("/")  # type: ignore[attr-defined]
    assert other.endpoint(area_page)(ok).content == b"rendered:a"

    redirected = rf.get("/")  # type: ignore[attr-defined]
    redirected.META["HTTP_X_REDIRECT"] = "1"
    assert other.endpoint(area_page)(redirected).content == b"went-elsewhere"

    # The direct-testing payoff: the decorated name IS the function, so a
    # direct call is arg-and-return typed with no indirection at all.
    page = area_page(Area(label="direct"), ok)
    assert_type(page, FakePage | HttpResponse)
    assert isinstance(page, FakePage)
    assert page.label == "direct"


def test_non_renderable_return_rejected(rf: object) -> None:
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="a")

    @area.view
    def area_bogus(a: Area, request: HttpRequest) -> HttpResponse:
        return None  # type: ignore[return-value]

    request = rf.get("/")  # type: ignore[attr-defined]
    with pytest.raises(TypeError, match="HttpResponse or a Template"):
        other.endpoint(area_bogus)(request)


def test_root_recoverable_beside_a_two_arity_page(rf: object) -> None:
    """A page that never mentions the root in its signature doesn't strand
    its URL-neighbors: the pinned sibling one word deeper binds TRoot
    through the Scope generics and receives it at runtime. Nesting under a
    page's URL is path= pins — the word repeats, visibly."""
    other = Router()

    @other.scope
    def area(request: HttpRequest) -> Area | HttpResponse:
        return Area(label="root-product")

    @area.scope
    def item(a: Area, *, thing_id: int) -> Thing | HttpResponse:
        return Thing(pk=thing_id)

    @item.view(path="page")
    def item_page(thing: Thing, request: HttpRequest) -> HttpResponse:  # 2-arity
        return _response(f"page:{thing.pk}")

    @item.view(path="page/deep")
    def item_page_deep(
        thing: Thing, root: Area, request: HttpRequest
    ) -> HttpResponse:  # 3-arity sibling one word below the 2-arity page
        return _response(f"deep:{thing.pk}:{root.label}")

    request = rf.get("/")  # type: ignore[attr-defined]
    assert (
        other.endpoint(item_page_deep)(request, thing_id=3).content
        == b"deep:3:root-product"
    )
