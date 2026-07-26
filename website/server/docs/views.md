# Views

Two files in every Django app drift apart: `views.py` and `urls.py`. Add a
view, forget the route. Rename a route, miss a `reverse()`. And a third thing
drifts worse than either: the permission checks copy-pasted at the top of every
view, where one missed `assert` is a security bug.

The router fixes all three at once. URLs are derived from your function names
and signatures, so there's nothing to keep in sync. And access control becomes
_structural_: you prove who the user is once, in one place, and every view
downstream receives that proof as a typed argument.

## Scopes

A _scope_ is a gate. It runs before any view underneath it, and it returns one
of three things:

- A **product**: a typed value proving the gate passed, handed to everything
  downstream.
- An **HttpResponse**: an early return, typically a redirect with a message.
- **`False`**: the canonical denial. The framework redirects to the login page
  with `next` set.

```python
from typing import Literal

from django.http import HttpRequest, HttpResponse

from reactivated.router import Router

from . import models

router = Router()


@router.scope
def books(request: HttpRequest) -> models.Member | HttpResponse | Literal[False]:
    if not request.user.is_authenticated:
        return False
    return models.Member.from_user(request.user)
```

That's the only place in the entire section that checks authentication.

## Views

Views hang directly off the scope. Their first argument is the scope's
product, already proven:

```python
@books.index
def books_list(member: models.Member, request: HttpRequest) -> HttpResponse:
    return BookList(books=member.books.all()).render(request)


@books.view
def books_export(member: models.Member, request: HttpRequest) -> HttpResponse:
    ...
```

Notice what's missing. No `@login_required`, no `request.user` in sight, no
assert at the top. A view that takes a `models.Member` cannot be reached
without one existing. That's not discipline, that's the type system.

The URLs came for free:

```
books/           -> books_list    (index: the scope's own URL)
books/export/    -> books_export  (the name minus the parent prefix, kebab-cased)
```

And `reverse()` names are simply the function names: `reverse("books_export")`.

## Parameterized scopes

Scopes nest. A child scope takes the parent's product plus keyword-only URL
parameters, and hangs off the parent the same way views do:

```python
@books.scope
def book(member: models.Member, *, book_id: int) -> models.Book | HttpResponse | Literal[False]:
    return get_object_or_404(member.books, pk=book_id)


@book.index
def book_detail(item: models.Book, request: HttpRequest) -> HttpResponse:
    ...


@book.view
def book_reviews(item: models.Book, member: models.Member, request: HttpRequest) -> HttpResponse:
    ...
```

The parameter annotation picks the URL converter, so the routes become:

```
books/<int:book_id>/           -> book_detail
books/<int:book_id>/reviews/   -> book_reviews
```

Two things worth noticing. The lookup goes through `member.books`, so "does
this book belong to this member" is checked exactly once, for every view under
the scope. And `book_reviews` takes a third argument: a view may also ask for
the _root_ product when it needs both.

## The built-in gates

Plain login checks are so common they ship with the router. `router.authenticated`
is a ready-made root scope whose product is your project's concrete `User`
type, via django-stubs:

```python
@router.authenticated.scope
def library(user: models.User, *, library_id: int) -> models.Library | Literal[False]:
    ...
```

There's also `router.maybe_authenticated`, the soft version: its product is
`User | None` and it never denies. Both work for [RPC](/documentation/rpc/)
as well.

## Refinement scopes

The pattern that pays for the whole system. Some views need more than "logged
in": billing configured, email verified, whatever your domain calls trusted.
Model that as a scope with an empty path that mints a `NewType`:

```python
from typing import NewType

Owner = NewType("Owner", models.Member)


@books.scope(path="")
def owner(member: models.Member, request: HttpRequest) -> Owner | HttpResponse:
    if member.billing_incomplete:
        messages.info(request, "Finish setting up billing first.")
        return redirect("books_list")
    return Owner(member)


@owner.view
def owner_billing(who: Owner, request: HttpRequest) -> HttpResponse:
    ...
```

`path=""` means the scope adds no URL segment; `owner_billing` lives at
`books/billing/`. But it demands an `Owner`, and the only place an `Owner` is
ever created is that one gate. Try to hang a billing view off the plain
`books` scope and mypy rejects it. The trust hierarchy is now a fact about
your types, not a convention in your code review checklist.

## Wiring it up

`urls.py` shrinks to a `mount()`:

```python
from reactivated import mount

from . import views

urlpatterns = [
    *mount(views),
    # ... anything else
]
```

`mount()` takes modules that own a `router` (or router instances directly) and
emits their URL patterns with _global_ duplicate detection: routes and reverse
names must be unique across everything mounted, pages and procedures alike. A
conflict is a boot error naming the culprits, instead of Django silently
first-matching one of them.

There's also `router.routes()`, which returns the `(route, name)` table. Drop
it into a snapshot test and your URL surface is under version control:

```python
def test_routes() -> None:
    assert router.routes() == [
        ("books/", "books_list"),
        ("books/export/", "books_export"),
        ("books/<int:book_id>/", "book_detail"),
        ("books/<int:book_id>/reviews/", "book_reviews"),
        ("books/billing/", "owner_billing"),
    ]
```

## Testing

The decorated name is the original function. Not a wrapper, not a callable
object: your function, with the signature you wrote. So testing view logic is
calling a function with a product you constructed:

```python
def test_book_detail(rf: RequestFactory, db: None) -> None:
    response = book_detail(book, rf.get("/"))

    assert response.status_code == 200
```

When you want the gates too — the full chain a URL would run —
`router.endpoint()` hands you the Django-callable for any registered view:

```python
def test_book_detail_requires_login(rf: RequestFactory) -> None:
    request = rf.get("/books/1/")
    request.user = AnonymousUser()

    response = router.endpoint(book_detail)(request, book_id=1)

    assert response.status_code == 302  # login redirect, with next set
```

No test client, no URL resolution, no middleware stack. Compare this to the
usual routine: a logged-in session, `reverse()`, and a full request cycle, all
to exercise thirty lines of view code. Here a view is a function, its gates
are functions, and tests call functions.

## Everything fails at boot

The router refuses to start, not to serve, when something is wrong. At import
time it checks:

- URL parameters must be annotated `int`, `str`, or `uuid.UUID`.
- View names must start with their parent's name: `book_reviews` under `book`,
  never `reviews`.
- Duplicate routes and duplicate reverse names are rejected — per router at
  registration, and across all routers at `mount()`.
- `path=` overrides may pin static words only. Parameters come from
  signatures, nowhere else.
- Scope and view arities are enforced, so a gate cannot silently take the
  wrong arguments.

A misnamed view is a `TypeError` on boot, not a 404 in production.

## The override hatch

Function names drive URLs, and one override exists: `path=` with static words,
for when the URL should not match the name.

```python
@books.view(path="reading-list")
def books_saved(member: models.Member, request: HttpRequest) -> HttpResponse:
    ...
```

One knob. If you find yourself wanting more, the framework is nudging you to
rename the function instead. It's usually right.

## Scopes gate procedures too

The same scope tree serves [RPC](/documentation/rpc/). `@book.rpc` declares a
procedure whose principal is the scope's product, gated by the identical
chain — with a transport-appropriate denial: pages redirect to login,
procedures return a 401. Prove who the user is once; every page _and_ every
procedure underneath inherits the proof.
