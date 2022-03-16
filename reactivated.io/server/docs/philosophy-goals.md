# Philosophy

Reactivated aims to be _the_ way to use Django and React together.

And we hold **strong** opinions and conventions. Here they are.

## Traditional server-rendered views work well

The tech world is currently leaning heavily on
[single-page-applications](https://en.wikipedia.org/wiki/Single-page_application) —
henceforth SPAs.

There's a time and place for these. It's not never, it's not nowhere. But it's not as
often as you'd think.

Are you creating a registration form? You don't need an SPA. You don't need to
immediately report `john` is not a valid email when the user hasn't had the chance to
type in the `@`. Same for the validity of the password.

Let them finish. Let them submit the form. Let the server validate it. You need to
validate on the server anyway. Then render the response.

Are you creating a map view where users can drag and place pins? A SPA sounds like a
good idea.

## Until they don't

Then the requirement finally comes in. You know exactly what I'm talking about. If the
user answers **Other** for **How did you hear about us?** when registering, show a
free-form field to write in the answer.

Reactivated makes this trivial. But we sprinkle dynamic behavior only when necessary.

## All roads lead to types

Save yourself a hard lesson. Any sufficiently dynamically-typed large project contains
an ad hoc, informally-specified, bug-ridden type-system using unit tests and assertions.

Use types from the start. They document your code. They catch bugs.

TypeScript is _amazing_. You'll never want to go back.

MyPy less so, but it's improving.

## Autoformat and lint everything

Waste no time [bike-shedding](https://en.wikipedia.org/wiki/Law_of_triviality).
Everything should be auto formatted and linted. Get back to writing your business logic.

## Colocation is a good thing

Do not confuse separation of concerns with separation of file types. Sure, your home
page CSS shouldn't live in the same file as your order processing logic. But isn't it
nice if the styles for your `Footer` component live alongside the markup? These are the
same concern.

Learn to love [colocation](https://kentcdodds.com/blog/colocation).

## Use cookies and sessions. You are not Google. You are not Uber.

Just use sessions. Don't waste your time with JSON Web Tokens. You don't need to be
stateless. Not yet. Probably never.

Trust me, PostgreSQL can handle looking up your sessions just fine. Stack Overflow
[ran for years](https://news.ycombinator.com/item?id=24970508) on a couple of SQL
servers.

JWT [introduce](https://news.ycombinator.com/item?id=13865459) complexities and deliver
[little value](https://news.ycombinator.com/item?id=27136539) in return.

Are you creating a platform for millions of users? Look into Redis as a session backend.
Still having performance issues? Then maybe look into JWT.

## REST is not the way. Not always. Practically never.

Yes, if you're loading a page listing every widget, go ahead and create a `/widgets/`
REST endpoint.

But it's likely your home page shows widgets, the current user, and your latest orders.
Why create `/widgets/`, `/orders/` and `/users/me/`?

Besides, another page may also show orders, but not just recent ones. Do you split
`/orders/` into `/recent-orders/` and `/orders/`? Do you add a filter so you can call
`/orders/?recent`?

This paradigm quickly breaks. It's best to stop thinking in terms of resources and go
back to thinking on pages and features.

What does the home page need? First think of the types of resources. But then gather
them all together in one endpoint.

```python
class HomePage(NamedTuple):
    orders: List[Order]
    profile: User
    widgets: List[Widget]
```

Now fulfill this interface:

```python
HomePage(
    orders=models.Objects.filter(created__gt=thirty_days_ago),
    profile=request.user,
    widgets=models.Widgets.filter(feature_on_home_page=True),
)
```

REST further crumbles when you need mutations. Why send full objects and resources when
creating or updating them? Take the classic example. Creating an order. REST tells us to
`POST` to `/orders/`. Instead of `/create-order/`. Subtle difference.

But you'll typically be asked send a full order payload. Is it the same fields that you
get when you `GET` and individual order? Is it fewer?

Ok you say, let's make fields some fields read-only. And some write-only.

And there you have it. The inputs don't match the outputs. They never will.

Think aloud: what information do I want when retrieving an order? And what information
do I want when creating an order? They're vastly different.

When creating an order, you really need minimal information: a list of items and
quantities.

When retrieving an order, you want all those quantities, all those items, their price,
their name and so forth.

Tying these to a _single_ isomorphic resource is futile.

What about GraphQL? It helps. Certainly it bundles things. But from my cursory
understanding, it's still _too_ generic. You want specificity, not re-usability.

In short: for your own internal use, REST is sometimes suitable for consuming.
Practically never for producing.

More on this soon.
