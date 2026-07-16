# Supporting pyright, basedpyright, and ty

Research notes on porting the `pick()` mypy plugin to the other type checkers.
Investigated July 2026 against pyright 1.1.411, basedpyright 1.39.9 (based on
pyright 1.1.411), and ty 0.0.59.

## What the mypy plugin actually does

The whole plugin reduces to one move. When mypy sees:

```python
class StagedMeal(pick(models.Meal, fields=["name", "hour"])):
    pass
```

the `get_dynamic_class_hook` in `reactivated/plugin.py` fires on the call to
`pick`. It computes a name from the defining module and class name
(`server.journal.nutrition` + `StagedMeal` becomes
`server_journal_nutrition_StagedMeal`), looks that up in the generated
`pick_schema` module, and swaps the symbol table entry for `StagedMeal` to
point at the generated class. If the generated symbol doesn't exist yet
(schema not regenerated), the class falls back to Any instead of erroring.

None of the other checkers have a plugin system, and none plan to add one.
pyright's docs reject plugins outright (`docs/mypy-comparison.md` in their
repo). ty's typing FAQ says the same, though they are adding hard-coded
support for specific libraries directly in core (pydantic already shipped).
So the question is: how hard is it to hard-code this one behavior in a fork?

Answer: not hard. The code is 100-300 lines in each. The real costs are fork
maintenance and distribution.

## Half the feature already works everywhere

`pick()` is annotated `-> Any`. All three checkers already tolerate an Any
base class silently:

- pyright pushes Any into `baseClasses` with no diagnostic
  (`typeEvaluator.ts`, in `getTypeOfClass`), and member lookup on a class
  with Any in its MRO degrades to Unknown (`typeUtils.ts`,
  `getClassMemberIterator`).
- ty converts a dynamic base into `ClassBase::Dynamic`
  (`types/class_base.rs`), producing an MRO of `[StagedMeal, Any, object]`.
  Attribute access falls back to the dynamic type.

So stock pyright, basedpyright, and ty give us the plugin's fallback behavior
today, unchanged. Only the positive half needs code: resolving the generated
class from `pick_schema` when it exists.

## One design change from the mypy plugin

The mypy plugin replaces the `StagedMeal` symbol wholesale. In both pyright
and ty, the natural move is to substitute the base class instead: the
`pick(...)` call's type becomes the generated class, and `StagedMeal` is an
ordinary subclass of it. Attribute typing, hover, completion, and
go-to-definition come out the same or better, it matches what actually
happens at runtime, and it avoids fighting each checker's declaration
machinery. Worth adopting if the mypy plugin is ever rewritten.

## pyright

Every piece needed already exists, with precedent:

- Special-casing calls by fully qualified name is routine.
  `analyzer/functionTransform.ts` is a post-call return-type rewriter
  dispatched on `functionType.shared.fullName` (used today for
  `functools.total_ordering`). This is structurally the same thing as mypy's
  dynamic class hook. `NamedTuple(...)`, functional `Enum(...)`, `NewType`,
  and 3-arg `type(...)` all go through similar dispatch in
  `typeEvaluator.ts`.
- Cross-module lookup exists: `getTypeOfModule(node, symbolName, nameParts)`
  in `typeEvaluator.ts` resolves a symbol from an arbitrary module. It powers
  `getTypingType`.
- The generated module gets pulled into the program automatically:
  `Program._lookUpImport` resolves and calls `addTrackedFile` for modules no
  user file imports. `pick_schema` just needs to be on the search path.
- Invalidation needs one line. Evaluator-time lookups create no import edge,
  so regenerating `pick_schema.py` would leave stale types in the language
  server. `sourceFile.ts` `_resolveImports` already injects implicit imports
  into every file (`builtins`, `_typeshed._type_checker_internals`); adding
  `pick_schema` there (with `skipMissingImport`) makes it a real dependency
  edge, and the standard file watcher handles the rest.

Estimate: 150-300 lines. A transform in `functionTransform.ts` (~60-100
lines), two lines to expose `getTypeOfModule` on the evaluator interface, one
line in `_resolveImports`, plus tests.

The catch is distribution. Pylance bundles its own closed pyright, so VS Code
users on Pylance can't use a fork. You'd ship the fork as its own language
server and point editors at it, which is exactly what basedpyright already
does. That makes forking plain pyright the worst option: same patch, but you
do the upstream tracking yourself and build the packaging story from scratch.

## basedpyright

The recommended target. Same insertion points as pyright (it tracks upstream
closely; they merge each pyright release tag, usually same day). What it adds:

- Packaging is solved. The build is `uv build` via a pdm-backend hook that
  webpack-bundles the language server into the Python package. One
  platform-independent wheel; Node comes from the `nodejs-wheel-binaries`
  dependency. No per-platform builds.
- The editor story is free. The stock basedpyright VS Code extension defaults
  `importStrategy` to `fromEnvironment`, launching `basedpyright-langserver`
  from the active venv. A forked wheel that keeps the module and entry-point
  names gets picked up by the unmodified extension.
- Their divergence from upstream shows this kind of patch is sustainable:
  ~19k added lines across `pyright-internal/src`, carried through weekly
  upstream merges by one maintainer. Our patch would be ~100-150 lines in two
  source files (`typeEvaluator.ts` or `functionTransform.ts`, plus
  `sourceFile.ts`) and rides along with their merges. Their
  `typeEvaluatorBased.test.ts` plus `samples/based_*` dirs are the exact
  pattern the tests would follow.

A generic version is also worth considering: a config option mapping a
dynamic-class factory's fullname to a generated module and a name template.
Framed as data rather than a code-execution plugin API, it's the kind of
thing that could plausibly land upstream in basedpyright itself, which would
retire the fork. Their pipeline runs a mypy_primer-style diagnostic diff
across many OSS projects on every PR, so a change like this is easy to prove
harmless.

## ty

The best patch and the worst fork, at least today.

The idiom for hard-coding library knowledge is a trio of enums matched by
fully qualified location: `KnownModule` (`ty_module_resolver/src/module.rs`),
`KnownClass` (`types/class/known.rs`), and `KnownFunction`
(`types/function.rs`). All three already contain third-party entries for
pydantic, and `types/dedicated/pydantic.rs` is over a thousand lines of
hard-coded pydantic model synthesis shipped in core, always on. The precedent
could not be stronger.

The swap itself:

- `infer_class_definition` (`types/infer/builder/class.rs`) is the insertion
  point. It already does a full symbol swap for `class NamedTuple` in the
  typing module, and it has the class name, file, and inferred base types in
  scope.
- Cross-module lookup exists: `resolve_module_confident` plus
  `imported_symbol` compose into exactly the needed helper
  (`known_module_symbol` in `place.rs` is a five-line template to copy).
- Invalidation is free. Module resolution and symbol lookup are salsa-tracked
  queries, so regenerating `pick_schema.py` automatically re-infers every
  class that consulted it. No bookkeeping. This is notably better than the
  mypy plugin, whose incremental-cache behavior around regenerated modules
  has always been the flaky part.
- Tests are markdown files with `# revealed:` assertions (mdtest), which
  makes them trivial to write.

Estimate: 150-300 lines across `module.rs`, `function.rs`, `place.rs`, and
`class.rs`, plus an mdtest file. No new salsa queries needed.

The problem is churn. ty is beta, versioned 0.0.x with breaking changes
allowed between any two releases, and `ty_python_semantic` sees roughly eight
commits a day, with class inference under active refactor. A fork means
conflicts on most rebases until it stabilizes. Their stated direction of
building library support directly into core means a well-specified
"generated-module redirect" mechanism might be sellable upstream eventually,
but that's a pitch, not a plan.

## Verdict

| | Patch | Fork burden | Distribution |
| --- | --- | --- | --- |
| pyright | ~150-300 lines | Weekly releases, tracked by you | Worst: Pylance is closed, no first-party wheel |
| basedpyright | ~100-150 lines | They merge upstream for you | Best: one wheel, stock extension finds it in the venv |
| ty | ~150-300 lines | Worst: pre-1.0, ~8 commits/day on the semantic crate | Fine: cargo build |

Fork basedpyright if we want this soon. Revisit ty once it stabilizes; its
salsa architecture genuinely fixes the invalidation problem and the patch is
the cleanest of the three.
