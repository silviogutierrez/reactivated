# Picks

Every full-stack app hits the same wall: the server knows your data, the client
doesn't. Somewhere in between, you end up writing serializers by hand and
praying the frontend types match.

Picks are Reactivated's answer. You declare exactly which fields of a model
cross the wire. Reactivated generates the matching TypeScript, validates the
data at runtime, and refuses to send anything you didn't declare.

Picks live in `reactivated.pick` and are backed by Pydantic. Shapes are real
classes: they validate, they serialize, and they exist on both sides of the
wire.

## Declaring a pick

Use `pick()` with a Django model and a list of fields:

```python
from reactivated.pick import pick

from . import models

BookSummary = pick(models.Book, fields=["id", "title", "author.name"])
```

Dot paths traverse relations. `author.name` follows the foreign key and picks
just the `name` off the related model.

For richer nested shapes, pass a tuple of the field name and another pick:

```python
AuthorDetail = pick(models.Author, fields=["id", "name", "bio"])

BookDetail = pick(
    models.Book,
    fields=["id", "title", ("author", AuthorDetail)],
)
```

## Input and output

A pick has two sides.

The _output_ side is what the server sends to the client: every declared field,
serialized from a model instance. The _input_ side is what the client is
allowed to send back. You get at them with `.output` and `.input`:

```python
validated = BookSummary.input.model_validate(payload)
```

Most of the time you won't touch these directly. RPC handlers and templates
use them for you. But the split matters when a field should only exist on one
side:

```python
BookForm = pick(
    models.Book,
    fields=["id", "title", "isbn", "internal_notes"],
    read_only_fields=["id"],
    write_only_fields=["internal_notes"],
)
```

`read_only_fields` exist only on the output. The client can see the `id` but
cannot submit one. `write_only_fields` are the reverse: the client can send
`internal_notes`, but the server never echoes them back.

## Returning model instances

Serializers usually force a dance: fetch the model, copy fields into a DTO,
return the DTO. With picks, you skip it. Annotate your return type with
`.returns` and hand back the Django instance directly:

```python
def featured_book() -> BookSummary.returns:
    return models.Book.objects.filter(featured=True).latest("created_at")
```

Reactivated serializes exactly the declared fields and nothing else. No
accidental leaks of columns you forgot the model had.

## Extra fields

Sometimes the shape needs a value that isn't a model field. A computed score,
a count from another query, whatever. Declare it with `extra_fields` and attach
it at return time with `.proxy()`:

```python
BookWithScore = pick(
    models.Book,
    fields=["id", "title"],
    extra_fields={"score": int},
)

def top_book() -> BookWithScore.returns:
    book = models.Book.objects.first()
    return BookWithScore.proxy(book, score=compute_score(book))
```

The proxy wraps the instance. Model fields resolve as usual, extras come from
what you passed in, and the TypeScript type includes both.

## Optional fields and stale clients

Here's a bug you only meet in production. You add a field to an input shape
and deploy. Every client still running the old bundle, and every mobile app
that hasn't updated, now omits that field on every request. Strict validation
rejects them all with a 400.

`optional_fields` is the escape hatch built for exactly this:

```python
SaveBook = pick(
    models.Book,
    fields=["id", "title", "subtitle"],
    optional_fields=["subtitle"],
)
```

On the input side, `subtitle` may be omitted entirely; an absent key
deserializes to `None`. On the TypeScript side it becomes `subtitle?: string |
null`. The output side is unaffected, since server data always has every
attribute.

> **Note**: `optional_fields` is restricted to nullable scalar model fields
> without a model default. After validation, an absent key and an explicit
> `null` are indistinguishable, and a model default would be shadowed by the
> implicit `None`.

## Hand-written picks

Not every shape maps to a model. Subclass `Pick` directly for a plain Pydantic
model that still participates in schema generation:

```python
from reactivated.pick import Pick


class SearchResult(Pick):
    id: int
    title: str
    rank: float
```

Because `Pick` is configured with `from_attributes`, you can still validate one
from any object with matching attributes, model or otherwise.

## Inline picks

For a one-off shape you will never reuse, skip the module-level assignment and
declare the pick inline in the annotation:

```python
from reactivated.pick import InlinePick

def rename(request: HttpRequest, form: InlinePick[models.Book, Literal["id", "title"]]) -> None:
    ...
```

## Enums and export()

Python enums pass through without ceremony. Annotate a field with the enum
class and it becomes a string union in TypeScript:

```python
class Format(enum.Enum):
    HARDCOVER = "Hardcover"
    PAPERBACK = "Paperback"
```

On the client, that field is typed `"HARDCOVER" | "PAPERBACK"`. Look closely:
those are the member _names_, not the values. Enums serialize and type by
name, and the rule is global. Any enum defined in one of your installed apps
speaks member names on every wire: pick fields, direct RPC returns, template
props. No registration step, nothing to remember. Names are identifiers;
values are display labels, and display labels don't belong in your protocol.

When accepting an enum as input, Pydantic validates the name automatically. No
mapping tables on either side.

> **Note**: The rule is about enums _you own_. Third-party enums (say, from
> an SDK's own Pydantic models) keep Pydantic's default value handling, so
> vendored libraries keep working untouched.

So where do the values come in? When the client needs the labels, `export()`
emits the runtime value map:

```python
from reactivated.pick import export

export(Format)
```

```typescript
server.store.models.Format.PAPERBACK; // "Paperback"
```

`export()` is never a serialization prerequisite. It exists to hand the
client the type and the label map, including for enums nothing else
references. There is one export path and one addressing scheme: everything
lands at its server location on the client (more on that below). Module-level
primitives export too, typed by their annotation. Non-primitives and duplicate
names are boot errors, not silent surprises.

## Deep picks and the mypy plugin

Time to address the obvious question. `BookSummary = pick(...)` is a function
call. How does mypy know the result has a `title`, let alone an `author` with a
`name` on it? Other frameworks stop here: serializer output is a dict, and deep
attribute access on it is unchecked. You get autocomplete on the model, then
fall off a cliff at the wire boundary.

The trick is that there is no trick. When Reactivated generates the client
code, it also generates `pick_schema`, a plain Python module with a genuine
class for every pick: real annotated fields, real nested classes for
relations, `input` and `output` both. Open the file and read it. It is
ordinary code.

The mypy plugin then does exactly one thing. When it sees a `pick()` assignment
in, say, `store/picks.py`, it looks up the matching generated class,
`pick_schema.store_picks_BookSummary`, and swaps that symbol in under your
name. `BookSummary` _is_ the generated class as far as mypy is concerned, so
`book.author.name` type-checks like any other attribute access, and so does
every level below it.

That's the entire plugin: a name substitution. No synthesized types, no
inference logic living inside the checker. Compare that to the heavyweight
plugins other Django tooling needs, where half the type system is reimplemented
in plugin hooks.

Enable it in `mypy.ini` alongside django-stubs:

```
plugins =
    mypy_django_plugin.main,
    reactivated.plugin
```

The lightness is the roadmap. Because everything real lives in generated,
ordinary Python, any type checker can already read it; what's missing elsewhere
is only the name swap. Getting that supported in Pyright and ty is where we
want to go, and a substitution this small is a much easier conversation than "please
run our type engine."

## The TypeScript side

Everything above lands in generated client code with one import and one
addressing scheme: the `server` namespace mirrors your Python tree, character
for character. Imports are _isomorphic_: the path you'd import on the server
is the path you use on the client. Same words, same order:

```python
from server.store.picks import BookSummary
```

```typescript
import {server} from "@reactivated";

type Book = server.store.picks.BookSummary.output;
type BookInput = server.store.picks.BookForm.input;
```

The same holds for everything the server declares. A procedure in
`server/store/api.py` is `server.store.api.rename(...)`. A template in
`server/store/templates.py` is `server.store.templates.BookDetail`. An
exported enum rides along at its module path too.

No registry of invented names, no guessing what codegen called something. If
you can write the Python import, you already know the client name. Jump-to-definition, grep, and code review all read the same on both
sides. One way to say everything.

And there's no drift to manage. Rename a field in Python and the TypeScript
compiler fails on every stale usage. That's the whole point: one declaration,
checked on both ends.
