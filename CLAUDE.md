# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reactivated is a Django + React framework providing a statically typed bridge between Django backends and React frontends. Python types (via `NamedTuple` classes decorated with `@template`, `@interface`, `@export`) are automatically converted to TypeScript interfaces, enabling zero-configuration full-stack development.

Monorepo workspaces: `packages/reactivated/` (core TS package), `reactivated/` (Python Django package), `sample/` (example app), `development/` (test environment), `website/` (docs).

## Development Commands

### Testing

```bash
./scripts/test.sh              # Run all checks (Python tests, lint, format, types)
./scripts/test.sh --server     # Python only: pytest, flake8, isort, black, mypy
./scripts/test.sh --client     # TypeScript only: prettier check
./scripts/test.sh --infrastructure  # Shell (shellcheck/shfmt) and Nix (nixfmt)
# E2E (--e2e) is currently a no-op

# Run a single Python test
pytest tests/forms.py
pytest tests/serialization.py -k "test_specific_name"

# Type checking
mypy --no-incremental .
npm exec tsc -- --noEmit
```

### Code Formatting

```bash
./scripts/fix.sh               # Auto-fix all git-changed files (py, ts, sh, nix)
./scripts/fix.sh path/to/file  # Fix a specific file
# Under the hood: autoflake + isort + black for Python, prettier for TS/JSON/YAML
```

### Building

```bash
cd packages/reactivated && npm run build  # Compile TS src/ → dist/ (just runs tsc)
```

## Architecture

### Type Generation Pipeline (the core mechanism)

This is the most important architectural concept. Python types flow to TypeScript through this pipeline:

1. **Registration**: `@template`, `@interface`, and `@export` decorators register types in global registries (`template_registry`, `interface_registry`, `value_registry` in `reactivated/serialization/registry.py`)
2. **Schema generation**: `reactivated/apps.py:get_schema()` collects all registered types, URLs, and context processors into a JSON Schema
3. **Code generation**: Schema is piped via stdin to `packages/reactivated/src/generator.mts`, which uses `json-schema-to-typescript` + `ts-morph` to produce TypeScript files
4. **Output**: Generated code lands in `node_modules/_reactivated/` (index.tsx, forms.tsx, context.tsx, urls.tsx, constants.tsx, template.tsx) — these are gitignored, regenerated on dev server start and on changes

### Dev Server Flow

When `manage.py runserver` runs, `reactivated/__init__.py` patches the process:

- Assigns Django to an internal port, gives Vite the user-facing port
- Runs type generation (`run_generations()`)
- Spawns Vite dev server (`npm exec start_vite`) which proxies non-asset requests to Django
- Spawns `tsc --watch --noEmit` for continuous type checking

### Key Python APIs (`reactivated/`)

- **`@template`** (`templates.py`): Decorates a `NamedTuple` to create a full-page React component. Adds `.render(request) -> TemplateResponse`. Component file must be at `client/templates/ClassName.tsx`.
- **`@interface`** (`templates.py`): Like `@template` but returns JSON (or HTML preview). Adds `.render(request)` and `.as_json(request)`.
- **`@export`** / **`export()`** (`__init__.py`): Exposes Python values (enums, primitives) to TypeScript as `constants` object. Use `@export(value=True)` on an `Enum` to make it available as `constants["app.Model.Enum"]` on the frontend, mapping enum names to values (e.g. `{NEW: "New", QUALIFIED: "Qualified"}`). Enums are serialized by **name** in JSON (e.g. `"NEW"`), not by value. When accepting an enum in an RPC input, type the field as the enum class directly (e.g. `status: Lead.Status`) — Pydantic validates automatically, no manual mapping needed.
- **`Pick[Model, "field1", "field2.nested"]`** (`pick.py`): Type-safe selective model field exposure with dot-path traversal support.
- **`serialization/`**: `create_schema()` converts Python types to JSON Schema definitions; `serialize()` converts instances to JSON-safe dicts. `registry.py` holds all global registries and `PROXIES` for built-in types.

### Key TypeScript modules (`packages/reactivated/src/`)

- `generator.mts` — The CLI that reads JSON schema from stdin and generates all `_reactivated` files
- `render.mts` — SSR using React 19 `renderToPipeableStream`; loads templates via `getTemplate`
- `vite.mts` — Vite dev server with Express middleware, proxies to Django
- `build.client.mts` — Production build: client bundle, optional django admin bundle, SSR renderer bundle
- `server.mts` — Production SSR server (Unix socket + Express)
- `forms/`, `components/` — Form and widget React components

### SSR Flow

- **Dev**: Django's `renderer.py` sends JSON payload via HTTP to Vite dev server (`/_reactivated/`), which SSR-renders via `render.mts`
- **Production**: `renderer.py` sends payload via Unix socket to `server.mts`, which runs the bundled renderer

## Testing

- **pytest** with `DJANGO_SETTINGS_MODULE=sample.server.settings`, test files in `tests/`
- **pytest-mypy-plugins**: Type-level tests (custom mypy.ini at `tests/mypy/mypy.ini`)
- **syrupy**: Snapshot testing (snapshots in `tests/__snapshots__/`)
- **Mypy plugin**: `reactivated/plugin.py` — hooks for `Pick` type analysis and `@template`/`@interface` decorator typing

## CI

When monitoring CI after a push, only wait for "Code tests" and the ubuntu integration test to pass. The macOS integration tests (macos-14, macos-15) are slow and verified manually — don't block on them.

## Environment

Uses Nix (`shell.nix`) for dependency management. Key env vars:

- `REACTIVATED_RENDERER` — SSR server address (skips spawning Vite if set)
- `REACTIVATED_SKIP_SERVER` — Disables dev server patching
- `REACTIVATED_SKIP_GENERATIONS` — Skips type generation
- `REACTIVATED_VITE_PORT` / `REACTIVATED_DJANGO_PORT` — Port coordination
- Django settings: `REACTIVATED_BUNDLES` (entry points, default `["index"]`), `REACTIVATED_ADAPTERS`, `REACTIVATED_IGNORED_URL_NAMESPACES` (default `["admin"]`)

## Code Style

- Prefer real type annotations over string ("quoted") annotations. Quote only to break a genuine circular import or forward reference — and note that router scopes/views resolve annotations at boot via get_type_hints, so quoted names must still be importable at runtime.

### Tests

Tests speak through their names and assertions — no narrating comments;
comments only for a trap the assertion cannot convey (e.g. why a behavior
must NOT happen).

Granular one-behavior tests are the default: each test is a distinct spec
sentence that would be missed if deleted. They are executable memory for
stateless agents, they fail simultaneously (one run = the full damage map),
and deleting one is diff-visible in a way that editing an assert inside a
combined scenario is not. Combined scenarios only when behaviors are
meaningless apart. No permutation spam — five tests for five file
extensions is coverage theater, not spec.

What deserves a test at all: mypy and CI do most of the work. Reserve unit
tests for regressions that actually happened and contracts the type system
cannot see (filesystem effects, ordering, deletion).

### Re-exports

Two blessed forms, in order of preference:

1. **Redundant alias** (the default): `from .core import FormField as FormField`,
   one name per statement — ruff's isort enforces the one-per-statement shape
   for aliased imports, and the alias marks the re-export as intentional (no
   `# noqa: F401`, ever).
2. **Plain import + `__all__`**: a single grouped `from .x import (a, b, c)`
   plus the names in `__all__`. Allowed when a file needs one positional
   import statement (e.g. ordering constraints); satisfies both F401 and
   mypy's `no_implicit_reexport`.

Facade modules (`reactivated.pick`, `reactivated.forms`) contain re-exports
only — implementation lives in submodules, imports stay at the top of the
file. Never suppress E402 to keep imports at the bottom; restructure instead.

### The export() rules

- One export path: `export(thing)` from `reactivated.pick`. Picks and type
  aliases emit types; **enums always emit both the type and the runtime
  value map** — labels that are secrets don't belong in an exported enum
  (export a `Literal` of the safe values instead). Module-level primitive
  values are typed by their annotation (`SNAP_LIST: list[Snap]`);
  non-primitives and duplicate names are boot errors.
- Everything app-derived is addressed by server location on the client:
  `server.journal.day.fast_init(...)` mirrors `server/journal/day.py`.
  Nothing app-derived is ever exported at the top level of `@reactivated`,
  and nothing is exported at two paths (one way to say everything).
- A namespace is a tree-shaking boundary: importing `server.core` pulls all
  of core's constants. That's fine _because_ exported values are primitives
  only — keep it that way.
