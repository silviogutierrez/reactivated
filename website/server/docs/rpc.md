# RPC

REST asks you to model your app as resources. But screens don't want
resources. They want use cases. A profile page needs three fields from three
tables, and the "right" REST design gives you three round trips or one bloated
endpoint pretending to be a resource.

We think the old MVC instinct was correct: one endpoint per use case. Think
`UpdateProfile`, not `UserResource`. Reactivated's RPC framework is that idea
with types: plain Python functions, validated inputs, and a generated
TypeScript client, so calling the server feels like calling a function.

## Your first RPC

Procedures register on the same `Router` that serves your
[views](/documentation/views/). Decorate a function, mount the router:

```python
from django.http import HttpRequest
from django.utils import timezone

from reactivated.router import Router

router = Router()


@router.rpc
def server_time(request: HttpRequest) -> str:
    return timezone.now().isoformat()
```

```python
# urls.py
from reactivated import mount

from . import api

urlpatterns = [
    *mount(api),
]
```

That's the entire backend. On the client, a typed function now exists at the
path mirroring the Python module. `server/store/api.py` becomes
`server.store.api`:

```typescript
import {server} from "@reactivated";

const result = await server.store.api.server_time();

if (result.type === "success") {
    console.log(result.data); // string, because Python said so
}
```

No fetch calls, no URL strings, no hand-written response types.

## Authentication

A bare `@router.rpc` is public: the request itself is the handler's first
argument. For everything else, the common case ships with the router:

```python
from reactivated.pick import Pick

from . import models


class ReviewForm(Pick):
    book_id: int
    rating: int
    comment: str = ""


@router.authenticated.rpc
def create_review(user: models.User, form: ReviewForm) -> None:
    book = models.Book.objects.get(pk=form.book_id)
    models.Review.objects.create(book=book, user=user, rating=form.rating)
```

Look at the handler's signature. It doesn't take a request. It takes your
project's concrete `User` (via django-stubs), and mypy holds you to it.
There's no `request.user` unwrapping, no `assert user.is_authenticated`
copy-pasted into every function, no decorator whose guarantees live only in
your memory. An anonymous caller gets a 401 and your handler never runs.

`router.maybe_authenticated` is the soft version: the handler receives
`User | None` and nobody is denied.

## Scopes gate procedures

Past plain authentication, access control is a _scope_: the same gates that
protect your [views](/documentation/views/). A scope proves something once and
returns a typed product; procedures registered on the scope receive that
product as their first argument:

```python
from typing import Literal


@router.scope
def staff(request: HttpRequest) -> HttpRequest | Literal[False]:
    if not request.user.is_staff:
        return False
    return request


@staff.rpc
def purge_cache(request: HttpRequest) -> None:
    ...
```

If the scope returns `False`, the framework responds with a 401 and
`{"error": "UNAUTHORIZED"}`. The same scope gates pages with a
transport-appropriate denial: views redirect to login, procedures get the 401.
One gate, both transports.

Scopes can resolve real objects too, so a whole family of procedures shares
one lookup. The [views documentation](/documentation/views/) covers scope
trees, products, and refinement in depth; everything there applies to
procedures as well.

## Inputs

The parameter after the principal is the body. Type it with a `Pick`, a
[pick's](/documentation/picks/) `.input` side, any Pydantic model, or even a
list of them:

```python
BookForm = pick(models.Book, fields=["id", "title", "isbn"], read_only_fields=["id"])


@router.authenticated.rpc
def update_books(user: models.User, forms: list[BookForm.input]) -> None:
    ...
```

Invalid input never reaches your code. The framework responds with a 400 and a
list of `{loc, msg}` errors, which the client receives as a typed `invalid`
result. Show them next to the offending fields and you have server-validated
forms with no duplicated validation logic.

Path parameters work too. Positional parameters annotated `int`, `str`, or
`uuid.UUID` become URL segments, and the generated client asks for them
first:

```python
@router.authenticated.rpc
def archive_book(user: models.User, book_id: int) -> None:
    ...
```

```typescript
await server.store.api.archive_book({book_id: 42});
```

Inputs can also carry form metadata. Decorate a `Pick` with `@form` and
declare fields with `FormField` to attach widget, label, and placeholder
information:

```python
from reactivated.forms import FormField, form


@form(exclude=["book_id"])
class ReviewForm(Pick):
    book_id: int
    rating: int = FormField(label="Rating")
    comment: str | None = FormField(widget="textarea", required=False)
```

`exclude` marks fields a rendered form should never show; the client supplies
`book_id` programmatically.

The metadata lands in the generated schema, so the client knows every field's
widget, label, and required state. What we don't have yet is documentation and
first-class helpers for _rendering_ it; projects currently read the schema and
build their own field components. That guide is coming.

## Outputs

Return anything serializable: primitives, Pydantic models, enums, lists, or a
pick's `.returns` to hand back Django instances directly:

```python
BookSummary = pick(models.Book, fields=["id", "title", "author.name"])


@router.query
def search_books(request: HttpRequest, query: str) -> list[BookSummary.returns]:
    return list(models.Book.objects.filter(title__icontains=query)[:20])
```

`router.query()` is the shorthand for read-only endpoints: GET, no
transaction.

Without `.returns`, the return type would be `BookSummary.output` and every
handler would end in ceremony:

```python
return [BookSummary.output.model_validate(book) for book in found]
```

Worse than ceremony, it's a typing hole. `model_validate` accepts `Any`, so
mypy will happily bless a call that validates the wrong object, and you find
out at runtime. With `.returns`, the declared return type _is_ the model
class. Hand back the wrong model and mypy flags the handler, not your pager.

## Handling the result

Every generated client function returns an `RPCResult<T>`, a discriminated
union you can exhaustively handle:

```typescript
const result = await server.store.api.create_review({book_id: 5, rating: 4});

if (result.type === "success") {
    // result.data is typed as the handler's return type
} else if (result.type === "invalid") {
    // result.errors: {loc: string[], msg: string}[]
} else if (result.type === "unauthorized") {
    // the scope said no: send them to login
}
```

The full union is `success`, `invalid`, `unauthorized`, `denied`, and
`exception`. Nothing is thrown for expected failures; the type forces you to
decide what a validation error looks like in your UI, at compile time.

## Options

The decorator takes a few knobs, all with sensible defaults:

```python
@staff.rpc(
    atomic_requests=True,   # default: one transaction spans scopes, validation, handler
    csrf_exempt=False,      # default
    methods=["POST"],       # default; add "GET" for cacheable reads
    log=False,              # False | True | "errors"
)
```

Handlers may be sync or async, and both honor `atomic_requests`: under the
default, writes roll back on error either way. Async handlers are bounced onto
the transaction thread to get there, since Django transactions are sync-only.
An async handler that needs the event loop (streaming, concurrent IO) and no
transaction should say so with `atomic_requests=False`; that's the natively
awaited path.

## Observing requests

For logging, metrics, or audit trails, register a single observer for the
whole router:

```python
from reactivated.rpc import RequestStatus, rpc_observer


@rpc_observer
async def observe(request, rpc_name, log, status, input, output, body, exception):
    if status is not RequestStatus.SUCCESS:
        logger.warning("rpc %s failed: %s", rpc_name, status)
```

The observer runs after every RPC with its name, its status (`SUCCESS`,
`INVALID`, `MALFORMED`, or `ERROR`), the parsed input and output, and the
exception if one escaped. One function, every endpoint, no middleware
archaeology.

## Testing

Here's the payoff of the principal design that nobody advertises: an RPC
handler is just a callable. The decorator registers it with the router and
hands it back untouched, with the same `(principal, form)` signature it was
written with. So in a test, you skip the router, the URL, and HTTP entirely:

```python
def test_create_review(db: None) -> None:
    user = models.User.objects.create_user("reader")
    book = models.Book.objects.create(title="Middlemarch")

    create_review(user, ReviewForm(book_id=book.pk, rating=4))

    assert book.reviews.count() == 1
```

No test client, no request factory, no mocking `request.user`. The handler
never wanted a request; it wanted a `User`, and you have one. Public handlers
accept whatever `RequestFactory` gives you, but for the common authenticated
case there's nothing to fake at all.

And the test is type-checked like everything else. Pass a misshapen form or
the wrong principal and mypy fails the test file before pytest ever runs it.
When you want the full HTTP treatment, validation, status codes and all, the
endpoint is still there for an integration test. But most of your coverage can
be plain function calls.

## Status codes, for the curious

A success is a 200. Validation failures are a 400 and arrive as `invalid`. A
denied scope is a 401, `unauthorized` on the client. The wrong HTTP method is
a 405. You'll rarely think about these; the generated client already did.
