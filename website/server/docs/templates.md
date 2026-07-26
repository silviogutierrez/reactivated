# Templates

Templates connect Django views to React components. You declare the props in
Python, render from your view, and write the markup in TSX. The full flow is
server-rendered; React hydrates on the client if and when you need
interactivity.

Templates are [picks](/documentation/picks/): Pydantic models whose fields are
the props your component receives. Same validation, same generated types, same
deep field access on both sides.

## Declaring a template

Subclass `Template` and annotate your props. By convention, templates live in
`templates.py` of the corresponding app:

```python
from reactivated.pick import pick
from reactivated.templates import Template

from . import models

BookSummary = pick(models.Book, fields=["id", "title", "author.name"])


class BookDetail(Template):
    book: BookSummary.returns
    review_count: int
    can_edit: bool
```

Note the `.returns` annotation: it means the view can pass the Django model
instance directly, and serialization picks out the declared fields. No manual
copying.

Django forms ride along too, via the `DjangoForm` bridge:

```python
from typing import Annotated

from reactivated.forms import DjangoForm


class BookReview(Template):
    book: BookSummary.returns
    form: Annotated[forms.ReviewForm, DjangoForm]
```

## Rendering from a view

The view stays idiomatic Django. Instantiate the template, call `.render()`:

```python
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404


def book_detail(request: HttpRequest, book_id: int) -> HttpResponse:
    book = get_object_or_404(models.Book, pk=book_id)

    return BookDetail(
        book=book,
        review_count=book.reviews.count(),
        can_edit=request.user.is_staff,
    ).render(request)
```

Need a different status code? Pass it:

```python
return NotFound(query=query).render(request, status=404)
```

There's also `render_to_string(request)` when you want the HTML itself, for
emails or fragments.

Because templates are Pydantic models, construction _validates_. Pass a wrong
type and you get an error at render time in Python, with a real traceback,
instead of `undefined` showing up three components deep in React.

## The React side

Each template expects a component at `client/templates/<ClassName>.tsx` with a
named `Template` export. Props come from the `server` namespace, at the path
mirroring the Python module that declared the template. A `BookDetail` in
`server/store/templates.py` is `server.store.templates.BookDetail`:

```typescript
import React from "react";

import {server} from "@reactivated";

export const Template = (props: server.store.templates.BookDetail) => (
    <div>
        <h1>{props.book.title}</h1>
        <p>by {props.book.author.name}</p>
        <p>{props.review_count} reviews</p>
        {props.can_edit && <a href="edit/">Edit</a>}
    </div>
);
```

Everything is typed. `props.book.author.name` is a `string` because the pick
said so. Try to read `props.book.isbn` and the compiler stops you, because the
pick never declared it.

## Components are checked against Python

Here's the part that saves you at refactor time. The generated code contains a
type-level assertion for every registered template: your component's props
must accept the shape Python declares. Rename `review_count` on the Python
side and `tsc` fails, pointing at `BookDetail.tsx`, before you have loaded a
single page.

This closes the classic gap in server-rendered setups, where the template and
the view drift apart silently and you find out from a user.

> **Note**: Set the `REACTIVATED_SKIP_TEMPLATE_CHECKS` environment variable to
> skip these assertions, for instance during a large migration.

## The entry point

One file boots the client: `client/index.tsx` calls `reactivate()`.

```typescript
import {reactivate} from "@reactivated";

reactivate();
```

Bare is the default behavior: parse the preloaded server data, resolve the
template, hydrate the document. Three optional hooks cover everything else:

```typescript
reactivate({
    // Browser-only setup, awaited before hydration. Analytics, cordova,
    // anything window-flavored belongs here as dynamic imports.
    init: async () => { ... },

    // Wraps the rendered template with your app providers. Runs during SSR
    // and in the browser — keep it pure so both sides agree on the markup.
    render: (content, info) => <AppProviders>{content}</AppProviders>,

    // Take over mounting entirely. Skip hydration, mount an SPA root,
    // whatever your app needs.
    mount: ({content}) => { ... },
});
```

During SSR the entry module is evaluated for its side effect, so its module
scope must stay node-safe. That's the whole reason `init` exists: it never
runs on the server.

## Templates inside the Django admin

The admin is too useful to give up and too rigid to restyle. Three `Template`
subclasses let you embed React into it instead of fighting it:

- `AdminView` renders a fragment embeddable in an admin page.
- `AdminChangeView` integrates with a model's change form. Call its
  `change_view(request, model_admin, object_id)` from your `ModelAdmin`.
- `AdminListView` does the same for the changelist.

On the client side, `reactivateAdmin()` hydrates the SSR'd fragment. It looks
for the framework's fragment marker and is a no-op when absent, so calling it
unconditionally from an admin entry is safe.

You keep the admin's authentication, navigation, and URLs, and render the one
screen that needs to be better than a stacked inline with React.
