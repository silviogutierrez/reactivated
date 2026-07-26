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
path mirroring the Python module — `server/store/api.py` becomes
`server.store.api`:

```typescript
import {server} from "@reactivated";

const result = await server.store.api.server_time();

if (result.type === "success") {
    console.log(result.data); // string, because Python said so
}
```

No fetch calls, no URL strings, no hand-written response types.

## Scopes are the access control

A bare `@router.rpc` is public: the request itself is the handler's first
argument. Everything else hangs off a _scope_ — the same gates that protect
your views. A scope proves something once and returns a typed _product_;
procedures registered on the scope receive that product as their first
argument, the _principal_:

```python
from typing import Literal


@router.scope
def merchant(request: HttpRequest) -> models.Merchant | Literal[False]:
    if not request.user.is_authenticated or not request.user.is_merchant:
        return False
    return models.Merchant.from_user(request.user)


class RenameForm(Pick):
    name: str


@merchant.rpc
def rename_shop(who: models.Merchant, form: RenameForm) -> None:
    who.shop.name = form.name
    who.shop.save()
```

Look at the handler's signature. It doesn't take a request. It takes a
`models.Merchant`, and mypy holds you to it. There's no `request.user`
unwrapping, no `assert user.is_merchant` copy-pasted into every function, no
decorator whose guarantees live only in your memory. If the scope returns
`False`, the framework responds with a 401 and your handler never runs.

The same scope gates pages, with a transport-appropriate denial: views
redirect to login, procedures return `{"error": "UNAUTHORIZED"}` with a 401.
One gate, both transports.

For the everyday case, the router ships with batteries:

```python
@router.authenticated.rpc
def create_review(user: models.User, form: ReviewForm) -> None:
    book = models.Book.objects.get(pk=form.book_id)
    models.Review.objects.create(book=book, user=user, rating=form.rating)
```

`router.authenticated` injects your project's concrete `User` (via
django-stubs) and denies anonymous callers. `router.maybe_authenticated` is
the soft version: `User | None`, never denies.

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

> **Note**: For richer inputs, `FormField()` from `reactivated.forms` attaches
> widget, label, and placeholder metadata to a field, so the client can render
> real form controls from the schema alone.

## Outputs

Return anything serializable: primitives, Pydantic models, enums, lists, or a
pick's `.returns` so you can hand back Django instances directly:

```python
BookSummary = pick(models.Book, fields=["id", "title", "author.name"])


@router.query(merchant)
def search_books(who: models.Merchant, query: str) -> list[BookSummary.returns]:
    return list(models.Book.objects.filter(title__icontains=query)[:20])
```

`router.query()` is the shorthand for read-only endpoints: GET, no
transaction.

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
@merchant.rpc(
    atomic_requests=True,   # default: one transaction spans scopes, validation, handler
    csrf_exempt=False,      # default
    methods=["POST"],       # default; add "GET" for cacheable reads
    log=False,              # False | True | "errors"
)
```

Handlers may be sync or async, and both honor `atomic_requests`: under the
default, writes roll back on error either way — async handlers are bounced
onto the transaction thread to get there, since Django transactions are
sync-only. An async handler that needs the event loop (streaming, concurrent
IO) and no transaction should say so with `atomic_requests=False`; that's the
natively awaited path.

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

| Scenario                  | Status | Client result  |
| ------------------------- | ------ | -------------- |
| Handler returns           | 200    | `success`      |
| Validation fails          | 400    | `invalid`      |
| The scope returns `False` | 401    | `unauthorized` |
| Wrong HTTP method         | 405    | —              |

You will rarely think about these. The generated client already did.
