"""Typed view routing: scopes, derived URLs, and statically-checked views.

The URL space is a tree. Params live only in Python signatures, never in
strings. Three registration verbs on a Router instance (imported by
urls.py — no autodiscovery, no global state):

- ``@router.scope`` — a resolution edge. Consumes its keyword-only URL
  kwargs, resolves objects once, returns a product (any value), an
  ``HttpResponse`` (rich failures stay responses), or ``False`` — the
  canonical denial: a login redirect with ``next``, the Django admin's
  semantics for unauthorized visitors.
- ``@router.view(parent)`` — a worded page. Receives ``(primary, root?,
  request, *, url_params)`` and returns an ``HttpResponse``.
- ``@router.index(parent)`` — a wordless page at the parent's own URL.
  Same contract as ``view``; contributes no leaf word.

Derivation rules (the complete list of magic):

1. A ``view``'s leaf word is its name minus the parent's prefix, snake ->
   kebab (``client_check_ins`` under ``client`` -> ``check-ins``). Every
   registered view and index — pinned or not — must extend its parent's
   prefix (boot error otherwise), so name<->URL consistency is
   unconditional; the remainder is free on indexes (``_list``,
   ``_detail``, ...).
2. Word scopes derive their word from their name; param scopes (those with
   keyword-only params) are wordless.
3. Function name = ``reverse()`` name, verbatim.

``path=`` is the single explicit override: static words only (never
params). On a ``view`` it pins the leaf words — multi-word is allowed
(``targets/create``), and pinned URLs survive function renames, so pin any
URL promised to the outside world. On a ``scope``, ``path=""`` declares a
wordless refinement edge. ``path=""`` on a ``view`` is an error: that's
``index``.

The view signature order is load-bearing, not taste: the trailing
``HttpRequest`` is the type-level anchor that terminates the checked
positional prefix before the ``ParamSpec`` tail. PEP 612 requires the
ParamSpec to be last in ``Concatenate`` (suffix checks are unwritable) and
offers no keyword-only remainder, so request-first would let ``P`` silently
swallow bogus positional params. Request-last makes them a mypy error.
"""

import inspect
import warnings
from typing import (
    Any,
    Callable,
    Concatenate,
    Generic,
    Literal,
    ParamSpec,
    TypeVar,
    get_args,
    get_origin,
    overload,
)

from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse
from django.urls import path as django_path
from django.urls.resolvers import URLPattern

from ..transport import DJANGO_CONVERTERS, resolved_hints, url_segment

P = ParamSpec("P")
Q = ParamSpec("Q")
TValue = TypeVar("TValue")
TChild = TypeVar("TChild")
TRoot = TypeVar("TRoot")

# Used only for parent-name stemming: children of a view named
# ``thing_detail`` derive against the ``thing_`` prefix. Never consulted to
# decide whether a view is an index — that's ``router.index``, explicitly.
INDEX_SUFFIXES = ("_list", "_detail")


def _deny(request: HttpRequest) -> HttpResponse:
    """The canonical denial: login redirect with ``next`` — the Django
    admin's own semantics for unauthorized visitors, authenticated or not.
    The authenticated-trespasser experience belongs to the login page
    (admin's says "authenticated as X, not authorized"); a scope that wants
    a 403 or a nag returns that response itself."""
    return redirect_to_login(request.get_full_path())


def _url_params(fn: Callable[..., object]) -> dict[str, type]:
    hints = resolved_hints(fn)
    params: dict[str, type] = {}

    for name, parameter in inspect.signature(fn).parameters.items():
        if parameter.kind is not inspect.Parameter.KEYWORD_ONLY:
            continue
        annotation = hints.get(name)
        if annotation not in DJANGO_CONVERTERS:
            raise TypeError(
                f"routing: {fn.__qualname__} URL param {name!r} must be "
                f"annotated int, str, or uuid.UUID (got {annotation!r})"
            )
        params[name] = annotation
    return params


def _positional_arity(fn: Callable[..., object]) -> int:
    return sum(
        1
        for parameter in inspect.signature(fn).parameters.values()
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    )


def _split_words(value: str) -> list[str]:
    return [word for word in value.split("/") if word]


def _stem(name: str) -> str:
    for suffix in INDEX_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


class _Node:
    def __init__(
        self,
        parent: "_Node | None",
        words: list[str],
        params: dict[str, type],
        scope_fn: "Callable[..., object] | None",
        scope_takes_request: bool = False,
    ) -> None:
        self.parent = parent
        self.words = words
        self.params = params
        self.scope_fn = scope_fn
        self.scope_takes_request = scope_takes_request

    def route(self) -> str:
        chain: list[_Node] = []
        node: _Node | None = self
        while node is not None:
            chain.append(node)
            node = node.parent
        pieces: list[str] = []
        for entry in reversed(chain):
            pieces.extend(entry.words)
            pieces.extend(
                url_segment(annotation, name)
                for name, annotation in entry.params.items()
            )
        if not pieces:
            return ""
        return "/".join(pieces) + "/"

    def scope_chain(self) -> "list[_Node]":
        chain: list[_Node] = []
        node: _Node | None = self
        while node is not None:
            if node.scope_fn is not None:
                chain.append(node)
            node = node.parent
        chain.reverse()
        return chain


class Scope(Generic[TValue, TRoot]):
    """Typed handle for a resolution edge. TValue is what it resolves;
    TRoot is the root scope's product, inherited down the whole chain."""

    def __init__(
        self, fn: Callable[..., object], node: _Node, takes_request: bool
    ) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.node = node
        self.takes_request = takes_request


class View(Generic[TValue, TRoot]):
    """A decorated view: a Django-callable that runs its scope chain, and a
    valid parent for further views."""

    def __init__(
        self,
        fn: Callable[..., HttpResponse],
        node: _Node,
        takes_root: bool,
    ) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.node = node
        self.takes_root = takes_root
        self.__name__ = fn.__name__
        self.__qualname__ = fn.__qualname__
        self.__module__ = fn.__module__
        self.__doc__ = fn.__doc__

    def __call__(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        product: object = request
        root_product: object | None = None

        for entry in self.node.scope_chain():
            scope_kwargs = {name: kwargs.pop(name) for name in entry.params}
            assert entry.scope_fn is not None
            if entry.scope_takes_request:
                result = entry.scope_fn(product, request, **scope_kwargs)
            else:
                result = entry.scope_fn(product, **scope_kwargs)
            if result is False:
                return _deny(request)
            if result is True:
                raise TypeError(
                    f"routing: scope {entry.scope_fn.__name__} returned True — "
                    f"scopes return a product, an HttpResponse, or False"
                )
            if isinstance(result, HttpResponse):
                return result
            product = result
            if root_product is None:
                root_product = result

        if self.takes_root:
            return self.fn(product, root_product, request, **kwargs)
        return self.fn(product, request, **kwargs)


def _build_scope(
    fn: Callable[..., object],
    parent: "Scope[Any, Any] | None",
    path: "str | None",
) -> "Scope[Any, Any]":
    params = _url_params(fn)
    if path is not None:
        if "<" in path or "{" in path:
            raise TypeError(
                f"routing: {fn.__name__} path= must contain static words only"
            )
        words = _split_words(path)
    elif params:
        words = []  # param scopes are wordless
    else:
        words = [fn.__name__.replace("_", "-")]

    arity = _positional_arity(fn)
    if parent is None:
        if arity != 1:
            raise TypeError(f"routing: root scope {fn.__name__} must take (request)")
        takes_request = False
    else:
        if arity not in (1, 2):
            raise TypeError(
                f"routing: scope {fn.__name__} must take (product) or "
                f"(product, request) before keyword-only URL params"
            )
        takes_request = arity == 2

    node = _Node(
        parent.node if parent is not None else None,
        words,
        params,
        scope_fn=fn,
        scope_takes_request=takes_request,
    )
    return Scope(fn, node, takes_request)


class ScopeBinder(Generic[TValue, TRoot]):
    def __init__(self, parent: "Scope[Any, Any] | None", path: "str | None") -> None:
        self._parent = parent
        self._path = path

    @overload
    def __call__(
        self,
        fn: Callable[
            Concatenate[TValue, HttpRequest, Q],
            "TChild | HttpResponse | Literal[False]",
        ],
    ) -> Scope[TChild, TRoot]: ...

    @overload
    def __call__(
        self,
        fn: Callable[Concatenate[TValue, Q], "TChild | HttpResponse | Literal[False]"],
    ) -> Scope[TChild, TRoot]: ...

    def __call__(self, fn: Callable[..., object]) -> "Scope[Any, Any]":
        return _build_scope(fn, parent=self._parent, path=self._path)


class ViewBinder(Generic[TValue, TRoot]):
    def __init__(
        self,
        router: "Router",
        parent_name: str,
        parent_node: _Node,
        url_path: "str | None",
        is_index: bool = False,
    ) -> None:
        self._router = router
        self._parent_name = parent_name
        self._parent_node = parent_node
        self._path = url_path
        self._is_index = is_index

    @overload
    def __call__(
        self, fn: Callable[Concatenate[TValue, TRoot, HttpRequest, P], HttpResponse]
    ) -> "View[TValue, TRoot]": ...

    @overload
    def __call__(
        self, fn: Callable[Concatenate[TValue, HttpRequest, P], HttpResponse]
    ) -> "View[TValue, TRoot]": ...

    def __call__(self, fn: Callable[..., HttpResponse]) -> "View[TValue, TRoot]":
        name = fn.__name__

        # Unconditional: registering on the router opts into the naming
        # scheme. ``path=`` pins the URL; it never relaxes the name — a
        # legacy view that can't conform yet stays a classic urls.py row.
        prefix = _stem(self._parent_name) + "_"
        if not name.startswith(prefix):
            raise TypeError(f"routing: {name} must start with {prefix!r}")

        if self._is_index:
            words = []
        elif self._path is not None:
            if "<" in self._path or "{" in self._path:
                raise TypeError(f"routing: {name} path= must contain static words only")
            words = _split_words(self._path)
            if not words:
                raise TypeError(
                    f"routing: {name} declares path='' — a wordless view is "
                    f"router.index, not a path override"
                )
        else:
            words = [name[len(prefix) :].replace("_", "-")]

        params = _url_params(fn)
        arity = _positional_arity(fn)
        if arity not in (2, 3):
            raise TypeError(
                f"routing: {name} must take (primary, request) or "
                f"(primary, root, request) before keyword-only URL params"
            )

        # View-parenting: any parent-view params the child uses must be
        # redeclared identically (name and annotation).
        parent_params = self._parent_node.params
        for param_name, annotation in params.items():
            if (
                param_name in parent_params
                and parent_params[param_name] is not annotation
            ):
                raise TypeError(
                    f"routing: {name} redeclares {param_name!r} with a "
                    f"different annotation than its parent"
                )
        own_params = {
            param_name: annotation
            for param_name, annotation in params.items()
            if param_name not in parent_params
        }

        node = _Node(self._parent_node, words, own_params, scope_fn=None)
        view = View[TValue, TRoot](fn, node, takes_root=arity == 3)
        self._router._register_view(view)
        return view


class Router:
    """Instantiate once per views module; ``urls.py`` imports the module and
    splats ``router.paths()``. Same registration mechanism as the RPC
    Router: no autodiscovery, no global registry, no circular imports."""

    def __init__(self) -> None:
        self._views: list[View[Any, Any]] = []
        self._known_nodes: dict[Callable[..., object], _Node] = {}

    def _register_view(self, view: View[Any, Any]) -> None:
        self._views.append(view)

    # -- scope ---------------------------------------------------------------

    @overload
    def scope(
        self,
        fn: Callable[
            Concatenate[HttpRequest, Q], "TValue | HttpResponse | Literal[False]"
        ],
        *,
        parent: None = None,
        path: "str | None" = None,
    ) -> Scope[TValue, TValue]: ...

    @overload
    def scope(
        self,
        fn: None = None,
        *,
        parent: Scope[TValue, TRoot],
        path: "str | None" = None,
    ) -> "ScopeBinder[TValue, TRoot]": ...

    def scope(
        self,
        fn: "Callable[..., object] | None" = None,
        *,
        parent: "Scope[Any, Any] | None" = None,
        path: "str | None" = None,
    ) -> object:
        if fn is not None:
            return _build_scope(fn, parent=None, path=path)
        return ScopeBinder(parent, path)

    # -- view ----------------------------------------------------------------

    def view(
        self,
        parent: "Scope[TValue, TRoot] | View[TValue, TRoot]",
        *,
        path: "str | None" = None,
    ) -> ViewBinder[TValue, TRoot]:
        return ViewBinder(self, parent.name, parent.node, path)

    def index(
        self,
        parent: "Scope[TValue, TRoot] | View[TValue, TRoot]",
    ) -> ViewBinder[TValue, TRoot]:
        """A wordless page at the parent's own URL. Takes no ``path=`` by
        construction — forgetting a word is a signature fact, not a check."""
        return ViewBinder(self, parent.name, parent.node, None, is_index=True)

    # -- emission ------------------------------------------------------------

    def routes(self) -> list[tuple[str, str]]:
        """The derived (route, reverse-name) table — also the snapshot-test
        surface."""
        seen_routes: dict[str, str] = {}
        seen_names: set[str] = set()
        table: list[tuple[str, str]] = []

        for view in self._views:
            route = view.node.route()
            if route in seen_routes:
                raise TypeError(
                    f"routing: duplicate route {route!r} "
                    f"({seen_routes[route]} / {view.name})"
                )
            if view.name in seen_names:
                raise TypeError(f"routing: duplicate reverse name {view.name!r}")
            seen_routes[route] = view.name
            seen_names.add(view.name)
            table.append((route, view.name))

        self._warn_untrimmable(seen_routes)
        return table

    def paths(self) -> list[URLPattern]:
        table = self.routes()
        by_name = {view.name: view for view in self._views}
        return [django_path(route, by_name[name], name=name) for route, name in table]

    def _warn_untrimmable(self, routes: dict[str, str]) -> None:
        for view in self._views:
            node = view.node
            if not node.words:
                continue
            parent = node.parent
            if parent is None:
                continue
            parent_route = parent.route()
            if parent_route and parent_route not in routes and parent.params:
                # Param node with a worded child but no page of its own:
                # a deliberate 404 hole is allowed; surface it once.
                warnings.warn(
                    f"routing: {parent_route!r} has static children but no "
                    f"page (advisory)",
                    stacklevel=2,
                )


def product_of(scope: Scope[TValue, Any]) -> type:
    """The non-HttpResponse arm of a scope's return annotation (introspection
    helper for tests and tooling)."""
    hints = resolved_hints(scope.fn)
    annotation = hints["return"]
    if get_origin(annotation) is not None:
        arms = [
            arm
            for arm in get_args(annotation)
            if arm is not HttpResponse and get_origin(arm) is not Literal
        ]
        if len(arms) == 1:
            return arms[0]  # type: ignore[no-any-return]
    return annotation  # type: ignore[no-any-return]


__all__ = ["Router", "Scope", "View", "ViewBinder", "product_of"]
