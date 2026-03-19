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
- **`@export`** / **`export()`** (`__init__.py`): Exposes Python values (enums, primitives) to TypeScript as `constants` object.
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

## Environment

Uses Nix (`shell.nix`) for dependency management. Key env vars:
- `REACTIVATED_RENDERER` — SSR server address (skips spawning Vite if set)
- `REACTIVATED_SKIP_SERVER` — Disables dev server patching
- `REACTIVATED_SKIP_GENERATIONS` — Skips type generation
- `REACTIVATED_VITE_PORT` / `REACTIVATED_DJANGO_PORT` — Port coordination
- Django settings: `REACTIVATED_BUNDLES` (entry points, default `["index"]`), `REACTIVATED_ADAPTERS`, `REACTIVATED_IGNORED_URL_NAMESPACES` (default `["admin"]`)
