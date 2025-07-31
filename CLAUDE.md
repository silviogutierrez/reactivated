# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reactivated is a Django + React framework that enables zero-configuration full-stack development. It provides a statically typed bridge between Django backends and React frontends, allowing developers to use both technologies without webpack configuration or complex tooling setup.

The codebase is structured as a monorepo with multiple workspaces:
- `packages/reactivated/` - Core TypeScript package
- `sample/` - Example application
- `website/` - Documentation site
- `development/` - Development environment
- `reactivated/` - Python Django package

## Development Commands

### Testing
```bash
# Run all tests (Python, linting, formatting)
./scripts/test.sh

# Run specific test categories
./scripts/test.sh --server    # Python tests only
./scripts/test.sh --client    # Frontend linting only
./scripts/test.sh --e2e       # E2E tests
./scripts/test.sh --infrastructure  # Shell/Nix linting
```

### Code Formatting
```bash
# Auto-fix formatting issues
./scripts/fix.sh

# Fix specific file
./scripts/fix.sh path/to/file.py
```

### Python Development
```bash
# Run Python tests
pytest

# Type checking
mypy --no-incremental .

# Code formatting
black .
isort .
flake8 .
```

### TypeScript Development
```bash
# Build TypeScript package
cd packages/reactivated && npm run build

# Type checking
npm exec tsc -- --noEmit

# Formatting
npm exec prettier -- --check '**/*.{ts,tsx,yaml,json}'
```

## Architecture

### Core Components

**Python Side (`reactivated/`):**
- `templates.py` - Template and interface decorators for React components
- `forms.py` - Enhanced Django forms with React integration
- `serialization/` - Type-safe serialization between Django and React
- `backend.py` - JSX template engine integration
- `renderer.py` - Server-side rendering coordination

**TypeScript Side (`packages/reactivated/`):**
- Vite-based build system with React and Vanilla Extract CSS
- Type generation from Django models and forms
- Client-side form handling and validation
- SSR coordination with Django

### Key Patterns

**Template System:**
- Use `@template` decorator for React components that render full pages
- Use `@interface` decorator for React components that return JSON APIs
- Templates are automatically registered and typed

**Form Integration:**
- Django forms are automatically serialized with full type safety
- React components receive typed form props
- Client-side validation mirrors Django form validation

**Type Safety:**
- Python types are automatically converted to TypeScript interfaces
- `Pick` utility for selective model field exposure
- `export()` function to expose Python values to React

## Project Structure

- `reactivated/__init__.py` - Main entry point with development server patching
- `reactivated/management/commands/` - Django management commands for builds
- `packages/reactivated/src/` - TypeScript source (gets compiled to `dist/`)
- `sample/` - Complete example showing typical usage patterns
- `development/` - Test environment for framework development

## Environment Setup

The project uses Nix for dependency management. Key environment variables:
- `REACTIVATED_RENDERER` - Controls SSR behavior
- `REACTIVATED_SKIP_SERVER` - Disables development server modifications
- `REACTIVATED_VITE_PORT` / `REACTIVATED_DJANGO_PORT` - Port coordination

## Build Process

1. TypeScript compilation creates `packages/reactivated/dist/`
2. Django management commands generate client assets
3. Vite handles bundling and development server
4. Python package includes compiled TypeScript assets