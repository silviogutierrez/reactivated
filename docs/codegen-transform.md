# codegen_transform: a declarative hook for generated types

Draft proposal to pitch to basedpyright and ty. It builds on the research in
[type-checkers.md](type-checkers.md), but nothing in it is reactivated-specific.
That's deliberate: it only lands if it covers other libraries too, the same way
dataclass_transform landed by covering attrs, pydantic, and SQLModel at once.

## The problem

Python is full of factories that build classes at runtime:

```python
class StagedMeal(pick(models.Meal, fields=["name", "hour"])):
    pass

UserForm = modelform_factory(User, fields=["email"])
Config = create_model("Config", retries=(int, ...))
```

Type checkers can't see through these. The return type depends on things
outside the expression: model metadata, a database, a schema file. So the
factory returns Any and the library ships an escape hatch instead of types.

There are two known ways out today, and both are bad.

The first is a plugin system. mypy has one, and reactivated uses it. But
plugins run third-party code inside the checker: they add latency to every
keystroke in the language server, they poison caches, they crash the host, and
they freeze internal APIs the checker wants to refactor. pyright and ty have
both said no to plugins, and having maintained a mypy plugin for years, I
can't blame them.

The second is hard-coding libraries into the checker, which is where ty is
headed (pydantic support already shipped in their core). It works, but it
doesn't scale past the top five packages on PyPI, and it will never reach a
library like this one.

## The observation

Look at what the reactivated mypy plugin actually does. It doesn't compute
types. It computes a *name*: take the module where `pick()` was called,
replace dots with underscores, append the class name, and look that up in a
generated module called `pick_schema`. The real type intelligence lives in
`pick_schema.py`, which is ordinary Python that a build step wrote to disk and
that any checker already analyzes with no special logic at all.

The arbitrary, messy, library-specific work (reading Django model metadata,
walking foreign keys, deciding nullability) happens at build time, in the
library's own process, where it can be tested and versioned and seen in diffs.
The only thing the checker is asked to do is resolve a symbol. That is the
checker working exactly as built, just with an updated reference.

Plugins run inside the checker. Transforms run before it. The missing piece is
a spec'd way for the checker to see the transform's output.

## The proposal

A decorator on the factory, declared once by the library author, shipped with
the package. No per-project configuration, same as dataclass_transform:

```python
@codegen_transform(
    module="pick_schema",
    name="{caller_module_underscored}_{binding_name}",
)
def pick(model: type[Model], *, fields: list[str]) -> type[Any]: ...
```

Semantics, kept narrow on purpose:

1. The hook applies only when the decorated callable is invoked as the entire
   base-class expression of a `class` statement, or as the entire right-hand
   side of a simple assignment. Anywhere else, the declared return type
   applies, unchanged.
2. `binding_name` is the class name (or the assignment target).
   `caller_module` is the module containing the call. The template language is
   a closed set of tokens with plain substitution. No conditionals, no
   expressions, no code. That restriction is the whole point: this stays data.
3. The checker resolves `module` through its normal import resolution, from
   the call site's file. It renders `name` and looks the symbol up. If it
   resolves to a class, that class is the type of the call expression (so in
   base position, the user's class becomes an ordinary subclass of it). If
   not, the declared return type applies.
4. At runtime the decorator is identity, like dataclass_transform.

Note what the fallback buys. The feature is strictly a refinement of the
declared return type, never a loosening. A checker that doesn't implement it
sees exactly what it sees today: Any. A checker that does implement it, but
finds no generated symbol (the user hasn't run codegen yet), also degrades to
today's behavior. And a checker can go one better than the mypy plugin ever
did: offer an opt-in diagnostic for "generated symbol not found," so strict
codebases can turn the silent Any into an error. Plugins never gave anyone
that.

## Who else this covers

Any library whose current answer is "sorry, that returns Any" plus a codegen
story:

- `pydantic.create_model(...)` is untypeable today. A sidecar that emits the
  concrete models makes it precise.
- Django's own `modelform_factory(Model, fields=[...])` is the identical
  shape.
- Functional `Enum("Color", names)` built from data files. SQL-first row
  types in the aiosql style. Any ORM or RPC layer that derives classes from a
  schema the checker can't read.

The pattern is "dynamic class factory plus codegen sidecar," and once you
start looking for it you see it everywhere.

## What the checker implements

Very little, and all of it with existing machinery. From the research in
type-checkers.md:

- pyright and basedpyright already dispatch on a callable's fully qualified
  name (`functionTransform.ts`), already resolve symbols from arbitrary
  modules (`getTypeOfModule`), and already pull unimported modules into the
  program on demand. The one real gap is an implicit import edge so that
  regenerating the module invalidates dependents, and there's in-tree
  precedent for that too. Around 150 lines total.
- ty gets invalidation for free: module resolution and symbol lookup are
  already salsa-tracked queries, so regenerating the file re-infers exactly
  the classes that consulted it. The insertion point
  (`infer_class_definition`) already does a full symbol swap for
  `typing.NamedTuple`. Similar line count.

No new caching, no sandboxing, no plugin API to stabilize. Projects that don't
use the decorator pay nothing.

## Objections

*Just import the generated class directly.* Then the generated name becomes
user-facing API and the factory call stops being the single source of truth.
Users write natural code; codegen mirrors it. The mypy plugins that exist are
the demand proof.

*Template micro-languages grow.* The token set is closed and versioned by the
spec. It starts at three tokens. dataclass_transform survived the same
pressure on field specifiers.

*Why not derive the type from the call arguments, dataclass_transform-style?*
Because in general you can't. `pick(models.Meal, fields=["name"])` depends on
what `Meal` declares in another file, and other factories depend on databases
or schema documents. That residue is exactly what plugins were covering, and
exactly what build time handles better.

*Soundness.* The checker trusts the generated file precisely as much as it
trusts any other source file on the path, because that's what it is. Checked
source, visible in diffs.

## How this lands

basedpyright first. They already ship basedtyping as the home for
checker-recognized extensions, so this arrives as
`basedtyping.codegen_transform` plus the ~150 line implementation. Show up
with the branch, tests in their sample format, and a diagnostic diff across
their OSS corpus proving it's inert unless opted into. Their CI makes that
claim checkable, which is worth more than any amount of persuasion.

ty second, argued in their own words. Their FAQ prefers "well-specified
features" over plugins, and this is one, smaller and more general than the
pydantic support they hand-wrote. Ship it behind ty_extensions, their existing
home for intrinsics. Part of the pitch is frankly economic: this is how they
avoid writing a thousand lines of core support per library forever.

Then the typing spec. dataclass_transform went typing_extensions experiment,
then PEP, then spec. Same path: two checker implementations, two or three
unrelated consumer libraries, then a write-up for the typing council as
dataclass_transform for code generators. mypy comes last, and the sell there
is retirement: this lets them deprecate the dynamic-class corner of the plugin
API, and it gives libraries like this one a single code path across every
checker.
