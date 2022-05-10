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
render(request, "my_template.html", {"book": book_instance, "form": form_instance})`
```

With Reactivated, we first declare our template structure:

```python
from reactivated import Pick, template

@template
class MyTemplate(NamedTuple):
    book: Pick[models.Book, "name"]
    form: forms.CommentForm
```

Then we render it like so, giving us an `HttpResponse`:

```python
MyTemplate(book=book_instance, form=form_instance).render(request)
```

### Models

Something surely stands out in the template above: we wrapped `Book` with `Pick` and
specified a `"name"` field. This is because we need to tell Reactivated what fields we
want sent to React from the model instance. You _cannot_ pass entire models as
Reactivated would have no way of knowing what fields you are going to use.

Think of `Pick` as a very quick way to create a serializer for your models.

### Forms

Unlike models, forms can be passed whole to your templates. Reactivated knows what to
do.

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

## The React Side

With your Python code declared above, Reactivated would expect a default export at
`client/templates/MyTemplate.tsx` for a React component that accepts the context you
declared. As you can see, types are automatically generated:

```typescript
import React from "react";

import {templates, Form} from "@reactivated";

export default (props: templates.MyTemplate) => (
    <div>
        <h1>{props.book.name}</h1>
        <form>
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

When using a React template, you'll have access to your `props` as declared using the
`template` decorator. But you can also access context processors by importing `Context`
and using `React.useContext`. Like everything else in Reactivated, this will be
statically typed.

```typescript
import React from "react";

import {templates, Context} from "@reactivated";

export default (props: templates.MyTemplate) => {
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

### AJAX

The tried-and-true [Post/Redirect/Get](https://en.wikipedia.org/wiki/Post/Redirect/Get)
workflow for forms will serve you well. But sometimes you want more dynamic, app-like
behavior. Enter AJAX.

From our example app, you can see how to use `fetch` and `FormData` to submit a form
without reloading the browser.

```python
def poll_comments(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, id=question_id)
    form = forms.Comment(
        request.POST or None, instance=models.Comment(question=question)
    )

    if form.is_valid():
        form.save()

        if request.accepts("application/json") is False:
            return redirect("poll_comments", question.pk)

    return templates.PollComments(question=question, form=form).render(request)
```

And a redacted version of the React template:

```typescript
export default (props: templates.PollComments) => {
    const {question} = props;
    const {request} = React.useContext(Context);
    const [comments, setComments] = React.useState(question.comments);
    const form = useForm({form: props.form});
    const title = `${props.question.question_text} comments`;

    const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const formElement = event.currentTarget;
        const formData = new FormData(formElement);

        const response = await fetch(request.path, {
            method: "POST",
            body: formData,
            headers: {
                Accept: "application/json",
            },
        });

        const data = (
            (await response.json()) as {props: templates.PollComments}
        ).props;

        setComments(data.question.comments);

        if (data.form.errors != null) {
            form.setErrors(data.form.errors);
        } else {
            form.reset();
        }
    };

    return (
        <Layout title={title}>
            <form
                action={request.path}
                method="post"
                onSubmit={onSubmit}
            >

                <Form as="p" form={form} />
                <button type="submit">Comment</forms.button>
            </form>
        </Layout>
    );
};
```

You'll notice this will work with our without JavaScript enabled. Moreover, data is
reloaded with a single request.

You can use our [setup script](/documentation/get-started/) to try out the full example
and review the code.

In the future, Reactivated will provide higher-level helpers to streamline this process
but this should illustrate the general flow.

### REST-style endpoint

We may want to create an AJAX only endpoint. Basically a read-only REST-style view that
serializes a model. This is easy to do using the `interface` decorator.

Inside `interfaces.py`:

```python
from typing import NamedTuple

from reactivated import interface, Pick

from . import models

@interface
class WidgetDetail(NamedTuple):
    widget: Pick[models.Widget, "name", "price"]
```

Then in our `views.py`:

```python
from . import models, interfaces

def widget_detail_api(request: HttpRequest, *, widget_id: int) -> HttpResponse:
    widget = get_object_or_404(models.Widget, pk=widget_id)
    return interfaces.WidgetDetail(widget=widget).render(request)
```

Assuming we connected this view to `/widgets/<int:question_id>/`, we could now use this
anywhere in the React side of things by importing `interfaces` from `@reactivated`

Here's a redacted example:

```typescript
import {interfaces} from "@reactivated";

const response = await fetch("/widgets/5/", {
    headers: {
        Accept: "application/json",
    },
});

const data: interfaces.WidgetDetail = await response.json();
const {widget} = data;
```

> **Note**: This is highly experimental. Reactivated will support first-class AJAX APIs
> with minimal code and strong type safety.

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
        -   templates
            -   MyTemplate.tsx
        -   books_app
            -   views.py
            -   models.py
            -   forms.py
            -   templates.py
            -   interfaces.py
```
