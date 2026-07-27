# Concepts

## Templates

Reactivated uses templates to connect your Django views to React components.

Unlike Django templates, the context of a Reactivated template is declared _explicitly_.

Not only does this document your code, but it ensures your React code is type-safe as
well.

### Rendering templates

Imagine we have a template that expects an instance of a `Book` model and a
`CommentForm` to leave a review.

Without Reactivated, we would render the template like so:

```python
render(request, "my_template.html", {"book": book_instance, "form": form_instance})
```

With Reactivated, we first declare our template structure:

```python
from typing import Annotated

from reactivated.forms import DjangoForm
from reactivated.pick import pick
from reactivated.templates import Template

from . import forms, models

BookPick = pick(models.Book, fields=["name"])


class MyTemplate(Template):
    book: BookPick.returns
    form: Annotated[forms.CommentForm, DjangoForm]
```

Then we render it like so, giving us an `HttpResponse`:

```python
MyTemplate(book=book_instance, form=comment_form).render(request)
```

### Models

Something surely stands out in the template above: we declared a _pick_ of `Book` with
just the `"name"` field. This is because we need to tell Reactivated what fields we
want sent to React from the model instance. You _cannot_ pass entire models as
Reactivated would have no way of knowing what fields you are going to use.

Think of a pick as a very quick way to create a serializer for your models. Except it
validates, generates TypeScript, and supports deep field access on both sides. Picks
are worth understanding well; they have [their own documentation](/documentation/picks/).

### Forms

Django forms can be passed to your templates through the `DjangoForm` annotation shown
above. Reactivated knows what to do: the form renders with its fields, errors, and
widgets fully typed on the React side.

## Views

Besides our special way to render a template, everything else in your view is standard
Django. The full view should look very similar to idiomatic Django with type
annotations:

```python
def comment_on_book(request: HttpRequest, *, book_id: int) -> HttpResponse:
    book_instance = get_object_or_404(models.Book, pk=book_id)
    comment_form = forms.CommentForm(request.POST or None)

    if comment_form.is_valid():
        # process comment

    return MyTemplate(book=book_instance, form=comment_form).render(request)
```

Classic `urls.py` wiring works exactly as you know it. But Reactivated also ships a
[router](/documentation/views/) that derives URLs from your function signatures and
makes access control structural. Use it when the bookkeeping starts to hurt.

## The React Side

With your Python code declared above, Reactivated would expect a `Template` export at
`client/templates/MyTemplate.tsx` for a React component that accepts the context you
declared.

Types are generated automatically under the `server` namespace, which mirrors your
Python tree: a template declared in `server/books_app/templates.py` is typed as
`server.books_app.templates.MyTemplate`.

```typescript
import React from "react";

import {Form, server} from "@reactivated";

export const Template = (props: server.books_app.templates.MyTemplate) => (
    <div>
        <h1>{props.book.name}</h1>
        <form method="POST">
            <Form as="p" form={props.form} />
            <button type="submit">Submit</button>
        </form>
    </div>
);
```

### Context

Context is a tricky word here. What Django
[calls context](https://docs.djangoproject.com/en/4.0/ref/templates/api/#rendering-a-context)
means the variables available for a template to use. In essence, what React would call
the `props`.

And what React [calls context](https://reactjs.org/docs/context.html) means `props` you
can access across components without having to pass them down the hierarchy manually.

Finally, Django has the concept of `context_processors` to allow you to automatically
include items, the request object, settings, and more into your template context.

The main examples are your CSRF token, the request object, and
[messages](https://docs.djangoproject.com/en/4.0/ref/contrib/messages/).

When using a React template, you'll have access to your `props` as declared on your
`Template` class. But you can also access context processors by importing `Context`
and using `React.useContext`. Like everything else in Reactivated, this will be
statically typed.

```typescript
import React from "react";

import {Context, server} from "@reactivated";

export const Template = (props: server.books_app.templates.MyTemplate) => {
    const context = React.useContext(Context);

    return (
        <div>
            <p>My static URL is {context.STATIC_URL}</p>
            <p>Currently, the following messages were supposed to be shown:</p>
            <pre>{JSON.stringify(context.messages, null, 4)}</pre>
        </div>
    );
};
```

Currently, only your own context processors and a few built-in ones are supported. If
you write your own context processor, be sure to add it to the `TEMPLATES` setting, and
make sure to properly annotate its return value.

### Dynamic behavior

The tried-and-true [Post/Redirect/Get](https://en.wikipedia.org/wiki/Post/Redirect/Get)
workflow for forms will serve you well. Server-rendered pages with full reloads get you
much further than the SPA industry admits.

When you do want app-like behavior (saving without a reload, live search, optimistic
UI), Reactivated has a first-class answer: [RPC](/documentation/rpc/). Declare a
procedure in Python, call it from TypeScript as a typed async function:

```python
@router.authenticated.rpc
def comment_on_book(user: User, form: CommentForm) -> None:
    ...
```

```typescript
const result = await server.books_app.api.comment_on_book({
    book_id: 5,
    comment: "A masterpiece.",
});
```

Inputs are validated, outputs are typed, and there are no endpoints, URLs, or response
shapes to hand-maintain. The [RPC documentation](/documentation/rpc/) covers the whole
system, including access control and testing.

## Project Structure

Reactivated encourages the following structure, but we
[want your comments](/documentation/rfc/):

```
-   BASE_DIR
    -   manage.py
    -   client
        -   index.tsx
        -   components
            -   Avatar.tsx
            -   Layout.tsx
        -   templates
            -   MyTemplate.tsx
    -   server
        -   settings
            -   common.py
            -   localhost.py
            -   production.py
        -   books_app
            -   views.py
            -   models.py
            -   forms.py
            -   templates.py
            -   api.py
```

Generated code lands in `client/generated/`: gitignored, regenerated on dev server
start, and pruned of orphans automatically. You never edit it, but you can always read
it.
