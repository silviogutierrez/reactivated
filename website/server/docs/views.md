# Views

Two files in every Django app drift apart: `views.py` and `urls.py`. Add a
view, forget the route. Rename a route, miss a `reverse()`. And a third thing
drifts worse than either: the lookup and permission checks copy-pasted at the
top of every view.

The router fixes all three. URLs derive from your function names and
signatures, so there's nothing to keep in sync. And the copy-pasted preamble
becomes a _scope_: resolve something once, and every view underneath receives
it as a typed argument.

## Scopes

A scope is shared resolution. It runs before any view underneath it, and
whatever it returns, the _product_, is handed down to every view and child
scope below.

No authentication yet. Watch what a scope does for a plain public site:

```python
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

from reactivated.router import Router

from . import models

router = Router()


@router.scope
def books(request: HttpRequest) -> QuerySet[models.Book]:
    return models.Book.objects.filter(published=True)
```

Every page in this section shows published books only. That rule now lives in
exactly one place.

Views hang directly off the scope, and their first argument is its product:

```python
@books.index
def books_list(published: QuerySet[models.Book], request: HttpRequest) -> HttpResponse:
    return BookList(books=list(published)).render(request)


@books.view
def books_search(published: QuerySet[models.Book], request: HttpRequest) -> HttpResponse:
    ...
```

The URLs came for free:

```
books/          -> books_list    (index: the scope's own URL)
books/search/   -> books_search  (the name minus the parent prefix, kebab-cased)
```

And `reverse()` names are simply the function names: `reverse("books_search")`.

## Parameterized scopes

Scopes nest. A child scope takes the parent's product plus keyword-only URL
parameters:

```python
@books.scope
def book(published: QuerySet[models.Book], *, book_id: int) -> models.Book | HttpResponse:
    return get_object_or_404(published, pk=book_id)


@book.index
def book_detail(item: models.Book, request: HttpRequest) -> HttpResponse:
    ...


@book.view
def book_reviews(item: models.Book, request: HttpRequest) -> HttpResponse:
    ...
```

The parameter annotation picks the URL converter, so the routes become:

```
books/<int:book_id>/           -> book_detail
books/<int:book_id>/reviews/   -> book_reviews
```

Notice the lookup goes through the parent's queryset. An unpublished book 404s
on every page under the scope, from one `get_object_or_404`. Still no auth in
sight: scopes earn their keep on structure and shared lookups alone.

When a view needs both products, declare a third parameter. The root scope's
product arrives as the second positional argument.

## Gates

Now the part everyone expects. A scope has three options, and only one of them
is a product:

- A **product**: proceed, hand it down.
- An **HttpResponse**: an early return, typically a redirect with a message.
- **`False`**: the canonical denial. The framework redirects to the login page
  with `next` set.

The everyday gate ships with the router. `router.authenticated` is a built-in
scope whose product is your project's concrete `User`, via django-stubs:

```python
@router.authenticated.scope
def shelf(user: models.User) -> QuerySet[models.SavedBook]:
    return user.saved_books.all()


@shelf.index
def shelf_list(saved: QuerySet[models.SavedBook], request: HttpRequest) -> HttpResponse:
    ...
```

An anonymous visitor never reaches `shelf_list`; they bounce to login. And the
view receives the user's own saved books, already filtered. There's no
`@login_required` because there's nothing to forget.

`router.maybe_authenticated` is the soft version: its product is `User | None`
and it never denies.

A custom gate is just a scope that can say no:

```python
from typing import Literal


@router.scope
def staff(request: HttpRequest) -> HttpRequest | Literal[False]:
    if not request.user.is_staff:
        return False
    return request
```

## Refinement scopes

One more trick, for when trust has grades. Some views need more than "logged
in": billing configured, email verified, whatever your domain calls trusted.
Model that as a scope with an empty path that mints a `NewType`:

```python
from typing import NewType

Subscriber = NewType("Subscriber", models.User)


@router.authenticated.scope(path="")
def subscriber(user: models.User, request: HttpRequest) -> Subscriber | HttpResponse:
    if not user.has_active_subscription:
        messages.info(request, "Subscribe to unlock this.")
        return redirect("books_list")
    return Subscriber(user)


@subscriber.view
def subscriber_billing(who: Subscriber, request: HttpRequest) -> HttpResponse:
    ...
```

`path=""` means the scope adds no URL segment; the view lives at `billing/`.
But it demands a `Subscriber`, and the only place one is ever minted is that
gate. Hang a billing view off a plain scope and mypy rejects it. The trust
hierarchy is now a fact about your types, not a convention in your code review
checklist.

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
        ("books/search/", "books_search"),
        ("books/<int:book_id>/", "book_detail"),
        ("books/<int:book_id>/reviews/", "book_reviews"),
        ("billing/", "subscriber_billing"),
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

When you want the gates too, the full chain a URL would run,
`router.endpoint()` hands you the Django-callable for any registered view:

```python
def test_shelf_requires_login(rf: RequestFactory) -> None:
    request = rf.get("/shelf/")
    request.user = AnonymousUser()

    response = router.endpoint(shelf_list)(request)

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
- Duplicate routes and duplicate reverse names are rejected, per router at
  registration and across all routers at `mount()`.
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
def books_saved(published: QuerySet[models.Book], request: HttpRequest) -> HttpResponse:
    ...
```

One knob. If you find yourself wanting more, the framework is nudging you to
rename the function instead. It's usually right.

## Scopes gate procedures too

The same scope tree serves [RPC](/documentation/rpc/). `@book.rpc` declares a
procedure whose principal is the scope's product, gated by the identical
chain, with a transport-appropriate denial: pages redirect to login,
procedures return a 401. Resolve once; every page and every procedure
underneath inherits it.
