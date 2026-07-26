"""Typed view routing: scopes, derived URLs, and statically-checked views.

The URL space is a tree, and it is WRITTEN as a tree: a Scope is a router
node, so children register on their parent, not on the router with a
kwarg. Params live only in Python signatures, never in strings. The
registration verbs (imported by urls.py — no autodiscovery, no global
state):

- ``@router.scope`` — a ROOT resolution edge. Consumes its keyword-only
  URL kwargs, resolves objects once, returns a product (any value), an
  ``HttpResponse`` (rich failures stay responses), or ``False`` — the
  canonical denial: a login redirect with ``next``, the Django admin's
  semantics for unauthorized visitors.
- ``@parent_scope.scope`` — a child resolution edge. Same contract; its
  first positional argument is the parent's product. Because the method
  lives on the parent, the parent's product type binds directly into the
  child-signature check, and cross-router parenting is unrepresentable.
- ``@parent_scope.view`` — a worded page. Receives ``(primary, root?,
  request, *, url_params)`` and returns an ``HttpResponse`` or an
  ``rpc.Template``, which the chain renders. Post/redirect/get reads as
  ``templates.X | HttpResponse``.
- ``@parent_scope.index`` — a wordless page at the parent's own URL.
  Same contract as ``view``; contributes no leaf word.

There is no view-parenting: a registered view is, deliberately, the
original plain function (direct calls are fully typed), so nothing hangs
off it. Nesting under a page's URL is spelled with ``path=`` pins on
siblings (``path="planner"`` for the page, ``path="planner/targets"``
for the thing beneath it) — the word repeats, visibly, and a typo 404s
instead of silently forking the URL space. A scope exists when its
resolution is SHARED (a gate for a subtree, an object with several
pages, an RPC access adapter); a lookup with a single consumer is just
the first line of its page, promoted to a scope when the second consumer
arrives. Scopes may carry both a pinned word and params
(``@parent.scope(path="truth")`` with ``*, uuid`` -> ``truth/<uuid>/``).

Like the RPC router, the decorators hand back the ORIGINAL FUNCTION:
direct calls are fully typed, args and return — you pass what the
signature says and call it. The chain-running Django callable (gates,
template rendering) is registered internally; URLs dispatch to it, and
``router.endpoint(fn)`` exposes it for tests that want the gates.

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
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Generic,
    Literal,
    ParamSpec,
    Protocol,
    TypeVar,
    get_args,
    get_origin,
    overload,
)

from asgiref.sync import async_to_sync
from django.http import HttpRequest, HttpResponse
from django.urls import path as django_path
from django.urls.resolvers import URLPattern

from .rpc.core import (
    RPC,
    RPCDecorator,
    RPCInput,
    RPCOutput,
    ScopeDenied,
    TAnonymous,
    TPrincipal,
    anyone,
    build_rpc_decorator,
)
from .templates import Template
from .transport import DJANGO_CONVERTERS, resolved_hints, url_segment

if TYPE_CHECKING:
    # `_User` is a django-stubs-only alias: the plugin rewrites it to the
    # project's AUTH_USER_MODEL at the CONSUMER's mypy run (even across a
    # py.typed boundary), so a framework-shipped `authenticated` scope injects
    # the project's concrete User. It does NOT exist at runtime, hence the
    # TYPE_CHECKING guard + string annotations; the built-in scopes below are
    # hand-constructed so reactivated never resolves these hints at runtime.
    # Older django-stubs lack `_User`; the ignore keeps reactivated's own
    # checks green (it degrades to Any there), while consumers on modern stubs
    # resolve their concrete User.
    from django.contrib.auth.models import _User  # type: ignore[attr-defined]

P = ParamSpec("P")
Q = ParamSpec("Q")
TValue = TypeVar("TValue")
TChild = TypeVar("TChild")
TRoot = TypeVar("TRoot")
R = TypeVar("R", bound="Template | HttpResponse")
# Variance-marked flavors for the protocols (mypy requires exact variance):
# primaries and the root are inputs (contravariant), returns are outputs
# (covariant).
TValue_contra = TypeVar("TValue_contra", contravariant=True)
TRoot_contra = TypeVar("TRoot_contra", contravariant=True)
R_co = TypeVar("R_co", bound="Template | HttpResponse", covariant=True)

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
    from django.contrib.auth.views import redirect_to_login

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
    """Typed handle for a resolution edge — and a router node: children
    (scopes, views, the index) register on it directly, which is what
    makes trees read as trees, binds the parent product type into every
    child-signature check, and leaves cross-router parenting with no
    spelling. TValue is what it resolves; TRoot is the root scope's
    product, inherited down the whole chain."""

    def __init__(
        self,
        fn: Callable[..., object],
        node: _Node,
        takes_request: bool,
        router: "Router[Any]",
    ) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.__module__ = fn.__module__
        self.node = node
        self.takes_request = takes_request
        self.router = router

    @overload
    def scope(  # async child scope (with request) — matched first
        self,
        fn: Callable[
            Concatenate[TValue, HttpRequest, Q],
            "Awaitable[TChild | HttpResponse | Literal[False]]",
        ],
    ) -> "Scope[TChild, TRoot]": ...

    @overload
    def scope(  # async child scope (no request)
        self,
        fn: Callable[
            Concatenate[TValue, Q], "Awaitable[TChild | HttpResponse | Literal[False]]"
        ],
    ) -> "Scope[TChild, TRoot]": ...

    @overload
    def scope(
        self,
        fn: Callable[
            Concatenate[TValue, HttpRequest, Q],
            "TChild | HttpResponse | Literal[False]",
        ],
    ) -> "Scope[TChild, TRoot]": ...

    @overload
    def scope(
        self,
        fn: Callable[Concatenate[TValue, Q], "TChild | HttpResponse | Literal[False]"],
    ) -> "Scope[TChild, TRoot]": ...

    @overload
    def scope(self, fn: None = None, *, path: str) -> "ScopeBinder[TValue, TRoot]": ...

    def scope(
        self,
        fn: "Callable[..., object] | None" = None,
        *,
        path: "str | None" = None,
    ) -> object:
        """A child resolution edge. Bare for the derived word (or
        wordlessness, for param scopes); ``path=`` pins words, and
        ``path=""`` declares a wordless refinement edge (a silent gate)."""
        if fn is not None:
            return _build_scope(fn, parent=self, path=None, router=self.router)
        return ScopeBinder(self, path)

    @overload
    def view(  # type: ignore[overload-overlap]
        self,
        fn: Callable[Concatenate[TValue, TRoot, HttpRequest, P], R],
    ) -> "RootViewFn[TValue, TRoot, P, R]": ...

    @overload
    def view(
        self,
        fn: Callable[Concatenate[TValue, HttpRequest, P], R],
    ) -> "ViewFn[TValue, P, R]": ...

    @overload
    def view(self, fn: None = None, *, path: str) -> "ViewBinder[TValue, TRoot]": ...

    def view(
        self,
        fn: "Callable[..., Any] | None" = None,
        *,
        path: "str | None" = None,
    ) -> Any:
        """A worded page under this scope. Bare for the derived leaf word
        (name minus this scope's prefix, snake -> kebab); ``path=`` pins."""
        binder: ViewBinder[TValue, TRoot] = ViewBinder(
            self.router, self.name, self.node, path
        )
        if fn is not None:
            return binder(fn)
        return binder

    @overload
    def index(  # type: ignore[overload-overlap]
        self,
        fn: Callable[Concatenate[TValue, TRoot, HttpRequest, P], R],
    ) -> "RootViewFn[TValue, TRoot, P, R]": ...

    @overload
    def index(
        self,
        fn: Callable[Concatenate[TValue, HttpRequest, P], R],
    ) -> "ViewFn[TValue, P, R]": ...

    def index(self, fn: Callable[..., Any]) -> Any:
        """The wordless page at this scope's own URL. Takes no ``path=``
        by construction — forgetting a word is a signature fact, not a
        check."""
        binder: ViewBinder[TValue, TRoot] = ViewBinder(
            self.router, self.name, self.node, None, is_index=True
        )
        return binder(fn)

    @overload
    def rpc(
        self,
        fn: Callable[Concatenate[TValue, RPCInput], RPCOutput],
    ) -> Callable[Concatenate[TValue, RPCInput], RPCOutput]: ...

    @overload
    def rpc(
        self,
        fn: None = None,
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
        atomic_requests: bool = True,
        methods: "list[Literal['GET', 'POST']] | None" = None,
    ) -> "RPCDecorator[TValue]": ...

    def rpc(
        self,
        fn: "Callable[..., Any] | None" = None,
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
        atomic_requests: bool = True,
        methods: "list[Literal['GET', 'POST']] | None" = None,
    ) -> Any:
        """A procedure on this scope: the chain resolves + gates, its product
        is injected as the handler's first arg (the principal), and a scope
        failure coerces to a JSON 401. Sugar for ``@router.rpc(scope)`` — the
        chain's params become URL segments, exactly as on a view."""
        decorator = self.router.rpc(
            self,
            csrf_exempt=csrf_exempt,
            log=log,
            atomic_requests=atomic_requests,
            methods=methods,
        )
        if fn is not None:
            return decorator(fn)
        return decorator


class View:
    """INTERNAL: the chain-running Django callable for a registered view.
    The decorator returns the original function (like the RPC router);
    this wrapper is what URLs dispatch to — reachable for tests and
    non-HTTP callers via ``Router.endpoint(fn)``."""

    def __init__(
        self,
        fn: Callable[..., object],
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

        for index, entry in enumerate(self.node.scope_chain()):
            scope_kwargs = {name: kwargs.pop(name) for name in entry.params}
            assert entry.scope_fn is not None
            fn = (
                async_to_sync(entry.scope_fn)
                if inspect.iscoroutinefunction(entry.scope_fn)
                else entry.scope_fn
            )
            if entry.scope_takes_request:
                result = fn(product, request, **scope_kwargs)
            else:
                result = fn(product, **scope_kwargs)
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
            # The root product is positional — entry 0's product — not the
            # first non-None one: a root scope may legitimately produce None.
            if index == 0:
                root_product = result

        if self.takes_root:
            result = self.fn(product, root_product, request, **kwargs)
        else:
            result = self.fn(product, request, **kwargs)
        if isinstance(result, HttpResponse):
            return result
        if isinstance(result, Template):
            return result.render(request)
        raise TypeError(
            f"routing: {self.name} returned {result!r} — views return an "
            f"HttpResponse or a Template"
        )


def _build_scope(
    fn: Callable[..., object],
    parent: "Scope[Any, Any] | None",
    path: "str | None",
    router: "Router[Any]",
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
    return Scope(fn, node, takes_request, router)


class RootScopeBinder:
    """Binder for ``@router.scope(path="...")``: a ROOT scope whose URL
    word comes from ``path`` instead of the function name — the way two
    subtrees share a word (a public tree and a principal-rooted staff tree
    both under ``annotate/``). The product doubles as the root product,
    exactly like the bare ``@router.scope`` form."""

    def __init__(self, path: "str | None", router: "Router[Any]") -> None:
        self._path = path
        self._router = router

    def __call__(
        self,
        fn: Callable[
            Concatenate[HttpRequest, Q], "TChild | HttpResponse | Literal[False]"
        ],
    ) -> Scope[TChild, TChild]:
        return _build_scope(fn, parent=None, path=self._path, router=self._router)


class ScopeBinder(Generic[TValue, TRoot]):
    """Binder for ``@parent_scope.scope(path="...")`` — the parametrized
    child form. The parent is always a Scope: root path-pinning is
    ``RootScopeBinder``, and parenting is spelled on the parent, never as
    a router kwarg."""

    def __init__(self, parent: "Scope[Any, Any]", path: "str | None") -> None:
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
        return _build_scope(
            fn, parent=self._parent, path=self._path, router=self._parent.router
        )


class ViewFn(Protocol[TValue_contra, P, R_co]):
    """The static face of a registered ``(primary, request)`` view. At
    runtime it IS the original function — direct calls are fully typed."""

    __name__: str

    def __call__(
        self,
        primary: TValue_contra,
        request: HttpRequest,
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R_co: ...


class RootViewFn(Protocol[TValue_contra, TRoot_contra, P, R_co]):
    """As ``ViewFn`` for ``(primary, root, request)`` views."""

    __name__: str

    def __call__(
        self,
        primary: TValue_contra,
        root: TRoot_contra,
        request: HttpRequest,
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R_co: ...


class ViewBinder(Generic[TValue, TRoot]):
    def __init__(
        self,
        router: "Router[Any]",
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
    def __call__(  # type: ignore[overload-overlap]
        self,
        fn: Callable[Concatenate[TValue, TRoot, HttpRequest, P], R],
    ) -> "RootViewFn[TValue, TRoot, P, R]": ...

    @overload
    def __call__(
        self,
        fn: Callable[Concatenate[TValue, HttpRequest, P], R],
    ) -> "ViewFn[TValue, P, R]": ...

    def __call__(self, fn: Callable[..., Any]) -> Any:
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
        view = View(fn, node, takes_root=arity == 3)
        self._router._register_view(view)
        # The RPC pattern: hand back the original function, untouched.
        # Direct calls are just calls; the chain lives behind endpoint().
        return fn


class _ScopeAdapter:
    """Runs a scope chain on behalf of an rpc endpoint. Any failure —
    ``False`` or an ``HttpResponse`` — coerces to the uniform denial: rpc
    callers get JSON, never redirects."""

    def __init__(self, scope: "Scope[Any, Any]") -> None:
        self.scope = scope
        self.chain_params: list[tuple[type, str]] = [
            (annotation, name)
            for entry in scope.node.scope_chain()
            for name, annotation in entry.params.items()
        ]
        self.has_async: bool = any(
            entry.scope_fn is not None and inspect.iscoroutinefunction(entry.scope_fn)
            for entry in scope.node.scope_chain()
        )

    def run(self, request: HttpRequest, kwargs: dict[str, Any]) -> Any:
        """Resolve the chain synchronously. Async scope functions are bounced
        through ``async_to_sync`` — so under an atomic request their ORM work
        re-joins the transaction thread (see the rpc execution matrix)."""
        product: object = request
        for entry in self.scope.node.scope_chain():
            entry_kwargs = {name: kwargs.pop(name) for name in entry.params}
            assert entry.scope_fn is not None
            fn = (
                async_to_sync(entry.scope_fn)
                if inspect.iscoroutinefunction(entry.scope_fn)
                else entry.scope_fn
            )
            if entry.scope_takes_request:
                result = fn(product, request, **entry_kwargs)
            else:
                result = fn(product, **entry_kwargs)
            if result is False or isinstance(result, HttpResponse):
                return ScopeDenied(result)
            if result is True:
                raise TypeError(
                    f"routing: scope {entry.scope_fn.__name__} returned True — "
                    f"scopes return a product, an HttpResponse, or False"
                )
            product = result
        return product


def _authenticated(request: HttpRequest) -> "_User | Literal[False]":
    """Built-in gate: the authenticated user, or the canonical denial. Its
    product types as the project's AUTH_USER_MODEL (see ``_User``)."""
    user = request.user
    return user if user.is_authenticated else False


def _maybe_authenticated(request: HttpRequest) -> "_User | None":
    """Built-in soft gate: the user if authenticated, else ``None`` — never
    denies. Product is ``User | None``."""
    user = request.user
    return user if user.is_authenticated else None


class Router(Generic[TAnonymous]):
    """The one router: pages (``scope``/``view``/``index``) and procedures
    (``rpc``/``query``) register on the same instance, share one
    route/reverse-name table, and mount together. No autodiscovery, no
    global registry, no circular imports."""

    @overload
    def __init__(self: "Router[HttpRequest]") -> None: ...

    @overload
    def __init__(self, request_type: type[TAnonymous]) -> None: ...

    def __init__(self, request_type: Any = HttpRequest) -> None:
        self.request_type = request_type
        self.handlers: dict[str, RPC] = {}
        self._views: list[View] = []
        self._builtin_scopes: dict[str, Scope[Any, Any]] = {}

    # -- built-in gates ------------------------------------------------------

    def _builtin(self, word: str, fn: Callable[..., object]) -> "Scope[Any, Any]":
        """A cached, hand-constructed root scope (no ``_url_params``/hint
        resolution, so the ``_User`` annotations never evaluate at runtime).
        Returned by identity so every use registers on one scope."""
        scope = self._builtin_scopes.get(word)
        if scope is None:
            node = _Node(None, [word], {}, scope_fn=fn, scope_takes_request=False)
            scope = Scope(fn, node, takes_request=False, router=self)
            self._builtin_scopes[word] = scope
        return scope

    @property
    def authenticated(self) -> "Scope[_User, _User]":
        """Built-in ``authenticated`` gate. Injects the project's concrete
        ``User`` (via django-stubs). Use as ``@router.authenticated.rpc`` /
        ``@router.authenticated.view`` — the batteries replacement for an
        ``authenticated`` access function."""
        return self._builtin("authenticated", _authenticated)

    @property
    def maybe_authenticated(self) -> "Scope[_User | None, _User | None]":
        """Built-in soft gate: injects ``User | None``, never denies."""
        return self._builtin("maybe_authenticated", _maybe_authenticated)

    # -- procedures ----------------------------------------------------------

    @overload
    def rpc(  # bare @router.rpc — public; the request is the principal
        self,
        access: Callable[Concatenate[TAnonymous, RPCInput], RPCOutput],
    ) -> Callable[Concatenate[TAnonymous, RPCInput], RPCOutput]: ...

    @overload
    def rpc(  # @router.rpc(scope) — gated; the scope product is the principal
        self,
        access: "Scope[TPrincipal, Any]",
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
        atomic_requests: bool = True,
        methods: "list[Literal['GET', 'POST']] | None" = None,
    ) -> RPCDecorator[TPrincipal]: ...

    @overload
    def rpc(  # @router.rpc() / @router.rpc(csrf_exempt=...) — public, with options
        self,
        access: None = None,
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
        atomic_requests: bool = True,
        methods: "list[Literal['GET', 'POST']] | None" = None,
    ) -> RPCDecorator[TAnonymous]: ...

    def rpc(
        self,
        access: Any = None,
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
        atomic_requests: bool = True,
        methods: "list[Literal['GET', 'POST']] | None" = None,
    ) -> Any:
        if isinstance(access, Scope):
            return build_rpc_decorator(
                self.handlers,
                scope_adapter=_ScopeAdapter(access),
                access=None,
                csrf_exempt=csrf_exempt,
                log=log,
                atomic_requests=atomic_requests,
                is_query=False,
                methods=methods,
            )
        # Public: the request itself is the principal (the identity gate).
        decorator = build_rpc_decorator(
            self.handlers,
            scope_adapter=None,
            access=anyone,
            csrf_exempt=csrf_exempt,
            log=log,
            atomic_requests=atomic_requests,
            is_query=False,
            methods=methods,
        )
        # Bare @router.rpc: `access` is actually the handler — register it now.
        return decorator if access is None else decorator(access)

    @overload
    def query(  # bare @router.query — public; the request is the principal
        self,
        access: Callable[Concatenate[TAnonymous, RPCInput], RPCOutput],
    ) -> Callable[Concatenate[TAnonymous, RPCInput], RPCOutput]: ...

    @overload
    def query(  # @router.query(scope)
        self,
        access: "Scope[TPrincipal, Any]",
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
    ) -> RPCDecorator[TPrincipal]: ...

    @overload
    def query(  # @router.query() / @router.query(csrf_exempt=...) — public
        self,
        access: None = None,
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
    ) -> RPCDecorator[TAnonymous]: ...

    def query(
        self,
        access: Any = None,
        *,
        csrf_exempt: bool = False,
        log: "Literal['errors'] | bool" = False,
    ) -> Any:
        if isinstance(access, Scope):
            return build_rpc_decorator(
                self.handlers,
                scope_adapter=_ScopeAdapter(access),
                access=None,
                csrf_exempt=csrf_exempt,
                log=log,
                atomic_requests=False,
                is_query=True,
            )
        decorator = build_rpc_decorator(
            self.handlers,
            scope_adapter=None,
            access=anyone,
            csrf_exempt=csrf_exempt,
            log=log,
            atomic_requests=False,
            is_query=True,
        )
        return decorator if access is None else decorator(access)

    def _register_view(self, view: View) -> None:
        self._views.append(view)

    def endpoint(self, fn: Callable[..., object]) -> Callable[..., HttpResponse]:
        """The chain-running Django callable for a registered view — what
        URLs dispatch to. For tests and non-HTTP callers that want the
        gates; if you already hold the principal, just call the function."""
        for view in self._views:
            if view.fn is fn:
                return view
        raise KeyError(f"routing: {fn!r} is not registered on this router")

    # -- scope ---------------------------------------------------------------

    @overload
    def scope(  # async root scope — matched first (unwraps the Awaitable)
        self,
        fn: Callable[
            Concatenate[HttpRequest, Q],
            "Awaitable[TValue | HttpResponse | Literal[False]]",
        ],
    ) -> Scope[TValue, TValue]: ...

    @overload
    def scope(
        self,
        fn: Callable[
            Concatenate[HttpRequest, Q], "TValue | HttpResponse | Literal[False]"
        ],
    ) -> Scope[TValue, TValue]: ...

    @overload
    def scope(
        self,
        fn: None = None,
        *,
        path: str,
    ) -> "RootScopeBinder": ...

    def scope(
        self,
        fn: "Callable[..., object] | None" = None,
        *,
        path: "str | None" = None,
    ) -> object:
        """A ROOT scope. Children register on the returned Scope
        (``@parent.scope`` / ``@parent.view`` / ``@parent.index``) — the
        router itself only ever plants roots."""
        if fn is not None:
            return _build_scope(fn, parent=None, path=path, router=self)
        return RootScopeBinder(path, self)

    # -- emission ------------------------------------------------------------

    def routes(self) -> list[tuple[str, str]]:
        """The derived (route, reverse-name) table for BOTH kinds — pages
        and procedures — with per-instance duplicate detection. Also the
        snapshot-test surface."""
        seen_routes: dict[str, str] = {}
        seen_names: set[str] = set()
        table: list[tuple[str, str]] = []

        for rpc_name, rpc_call in self.handlers.items():
            seen_routes[rpc_call["url"]] = rpc_name
            seen_names.add(rpc_name)
            table.append((rpc_call["url"], rpc_name))

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
        by_name: dict[str, Any] = {view.name: view for view in self._views}
        patterns: list[URLPattern] = []
        for rpc_name, rpc_call in self.handlers.items():
            patterns.append(
                django_path(rpc_call["url"], rpc_call["handler"], name=rpc_name)
            )
        for route, name in table:
            if name in by_name:
                patterns.append(django_path(route, by_name[name], name=name))
        return patterns

    def contributing_modules(self) -> set[str]:
        """The modules that registered scopes, views, or rpcs on this router —
        the provenance ``mount()`` verifies so a listed-but-empty module is a
        boot error. rpcs and views record their defining module directly;
        scopes are picked up from the chains of the views under them."""
        modules: set[str] = set()
        for rpc_call in self.handlers.values():
            modules.add(rpc_call["module"])
        for view in self._views:
            modules.add(view.__module__)
            for node in view.node.scope_chain():
                if node.scope_fn is not None:
                    modules.add(node.scope_fn.__module__)
        return modules

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


__all__ = [
    "RootViewFn",
    "Router",
    "Scope",
    "ViewFn",
    "product_of",
]
