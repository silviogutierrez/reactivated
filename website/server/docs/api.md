# API

Reactivated provides you with an API to make working with Django and React easier.

## Python / Django

### `reactivated.template`

Use the `template` decorator to define your template structure. By convention, these
templates go in `templates.py` of the corresponding app. Simply import `NamedTuple` and
`template` then define the context.

```python
from typing import NamedTuple

from reactivated import template

@template
class MyTemplate(NamedTuple):
    name: str
    title: str
    age: int
    location: str
```

From a standard Django view, render your template by instantiating it and calling
`render` on it.

```python
from django.http import HttpRequest, HttpResponse

from . import templates

def my_view(request: HttpRequest) -> HttpResponse:
    return templates.MyTemplate(
        name="George Washington",
        title="President",
        age=67,
        location="Virginia",
    ).render(request)

```

> **Note**: Reactivated will look for a **default export** from
> `BASE_DIR/client/templates/TEMPLATE_NAME.tsx`

### `reactivated.Pick`

Passing model instances to a React template is tricky. We need to serialize the model
instance, but for many reasons, can't simply send over every field. Instead, we
explicitly tell our template what fields to pick from the model.

Using the following models:

```python
class Author(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()

class Book(models.Model):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=100)
```

We can use `Pick` as follows:

```python
from reactivated import Pick, template
from typing import Literal

from . import models

@template
class BookDetail(NamedTuple):
    book: Pick[models.Book, Literal["name", "author.name", "author.age"]]
```

To use a list of book instances, just wrap everything with `List` from `typing`:

```python
@template
class BookDetail(NamedTuple):
    book: Pick[models.Book, Literal["name", "author.name", "author.age"]]
    related_books: List[Pick[models.Book, Literal["name", "author.name", "author.age"]]]
```

You'll notice we're repeating ourselves quite a bit. We can alias our `Pick` and reuse
it:

```python
Book = Pick[models.Book, Literal["name", "author.name", "author.age"]]

@template
class BookDetail(NamedTuple):
    book: Book
    related_books: List[Book}
```

We would then render the template as follows:

```python
def book_detail(request: HttpRequest, *, book_id: int) -> HttpResponse:
    book = get_object_or_404(models.Book, id=book_id)
    return BookDetail(
        book=book,
        related_books=list(book.related_books.all()),
    ).render(request)
```

### `reactivated.interface`

This behaves identically to the `template` decorator. But unlike `template`, it will not
expect you to create a corresponding `.tsx` file.

This is useful for creating AJAX-only endpoints and statically typing them.

See the [AJAX concepts](/documentation/concepts/) for more information.

## TypeScript / React

### `templates`

When you use the `reactivated.template` decorator in your Django code, Reactivated will
generate types for you.

For a template named `MyTemplate` inside `server/custom_app/templates.py`, you would
then create a file named `client/templates/MyTemplate.tsx` and import `templates` like
so:

```typescript
import {templates} from "@reactivated";

export const Template = (props: templates.MyTemplate) => (
    <div>{props.properties_of_my_template}</div>
);
```

If you mismatch types, say `templates.MyOtherTemplate` and they are
[structurally](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)
different, TypeScript will complain. If you don't create the template file or don't
export the template correctly, TypeScript will also complain.

### `Form`

Just like Django templates, you can import `Form` and render a basic form as `p` tags or
a table. Just like Django's renderer, the outer `form` tag is _not_ included. Same goes
for the `table` tag.

```typescript
import {CSRFToken, Form, templates} from "@reactivated";

export default (props: templates.MyFormTemplate) => (
    <div>
        <form method="POST">
            <CSRFToken />
            <Form form={props.form} as="p" />
            <button type="submit">Submit</button>
        </form>

        <form method="POST">
            <CSRFToken />
            <table>
                <tbody>
                    <Form form={props.form} as="table" />
                </tbody>
            </table>
            <button type="submit">Submit</button>
        </form>
    </div>
);
```

### `useForm`

You'll probably want far more control over the rendering of your form. And if you have
any custom form widgets, the built-in `Form` tag will complain as it does not know how
to render them.

The `useForm` hook exposes values, errors, fields and more. This gives you full control
over the output.

Because you have access to `form.values`, this also allows you to manipulate the form
dynamically.

```typescript
import {CSRFToken, Widget, useForm, FieldHandler, templates} from "@reactivated";

const Field = (props: {field: FieldHandler}) => {
    const {field} = props;
    const widget =
        field.tag == "custom_app.widgets.CustomWidget" ? (
            <CustomWidget field={field} />
        ) : (
            <Widget field={field} />
        );

    return (
        <div>
            <label>
                <div>{field.label}</div>
                {widget}
            </label>
        </div>
    );
};

export default (props: templates.MyFormTemplate) => {
    const form = useForm({form: props.form});

    return (
        <form method="POST">
            <CSRFToken />
            {form.nonFieldErrors?.map((error, index) => (
                <div key={index}>{error}</div>
            ))}
            {form.hiddenFields.map((field, index) => (
                <Widget key={index} field={field} />
            ))}
            <Field field={form.fields.username} />
            <Field field={form.fields.password} />
            <Field field={form.fields.country} />
            {form.values.country === "USA" && <Field field={form.fields.zip_code} />}
        </form>
    );
};
```

Notice we declare a custom field component using the `FieldHandler` convenience type.
The type system will _force_ us to handle custom widgets before delegating to the
built-in `Widget` component. In most cases, you'll end up providing custom widget markup
even for built-in widgets, but the `Widget` component helps you get started.

### `FormSet`

Just like the `Form` tag, you can use the `FormSet` component to quickly prototype your
form sets.

```typescript
import {CSRFToken, FormSet, templates} from "@reactivated";

export default (props: templates.MyFormSetTemplate) => (
    <div>
        <form method="POST">
            <CSRFToken />
            <table>
                <tbody>
                    <FormSet formSet={props.formSet} as="table" />
                </tbody>
            </table>
            <button type="submit">Submit</button>
        </form>
    </div>
);
```

### `useFormSet`

For more control over form sets, you can use the `useFormSet` hook. This will expose
each form in the form set under `forms`. From then on, you can render the forms manually
as with the `useForm` example. But don't forget `ManagementForm`.

```typescript
import {CSRFToken, useFormSet, ManagementForm, templates} from "@reactivated";

export default (props: templates.MyFormSetTemplate) => {
    const formSet = useFormSet({formSet: props.formSet});

    return (
        <form method="POST">
            <CSRFToken />
            <ManagementForm formSet={props.formSet} />
            {formSet.forms.map((form) => (
                // Render each form
            ))}
            <button type="button" onClick={formSet.addForm} />
        </form>
    );
};
```

Note that for convenience, `useFormSet` also exposes an `addForm` method to dynamically
add a form to the form set.

Just like `useForm`, `useFormSet` exposes the values of each form under `values`.

### `reverse`

Yes, it's magic. You can use `reverse` just like you can in your Django code.

All your **named** views will be there with full static types.

Take the following `urls.py` file:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_page, name="home_page"),
    path("blog/<str:post_slug>/", views.post_detail, name="post_detail"),
    path("widgets/<int:widget_id>/", views.widget_detail, name="widget_detail"),
]
```

Reverse will expect the following fully type-safe code:

```typescript
import {reverse} from "@reactivated";

// No arguments. If you pass any, TypeScript will not compile.
reverse("home_page");

// An argument of type string with the name post_slug is expected
reverse("post_detail", {post_slug: "you-might-not-need-jwt"});

// An argument of type number with the name widget_id is expected
reverse("widget_detail", {widget_id: 3});
```

When your code executes, the right URLs will be resolved for you.

> **Warning**: We need your
> [thoughts and feedback](https://github.com/silviogutierrez/reactivated/discussions/154)
> on the `reverse` API. There are potential security considerations.

## Scripts

### Formatting

Formatting and linting should not occupy your time. Reactivated bundles `prettier`,
`eslint`, `black`, `flake8`, and `isort` to solve this for you.

There's no configuration, just run the below script to fix all the formatting in your
application:

```bash
scripts/fix --all
```

You can also fix an individual file by passing the file, like so:

```bash
scripts/fix --file client/templates/MyTemplate.tsx
```

If you run `scripts/fix.sh` without any arguments, it will try to fix everything that
has changed against the `main` branch of your repository.

### Testing

You can test your application, including linting and formatting by running
`scripts/test.sh`.

Try running it on the example project to see everything passing. Then try breaking it.

You can test only React code and Django code by using the `--client` and `--server`
flags, respectively.
