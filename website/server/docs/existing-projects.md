# Existing projects

Our [all-in-one setup script](/documentation/getting-started/) is the best way to use
Reactivated.

But at its core, Reactivated can be installed from **npm** and **PyPI** just like any
other packages.

## Requirements

- Python 3.12
- Django 5.1
- A current Node.js LTS
- PostgreSQL

Make sure the `python` and `node` executables are available in your `PATH`. Reactivated
will invoke them as needed.

Strictly speaking, Reactivated may run with other versions of these requirements. In
fact, you can use any database you want. But custom fields and certain features depend
on the exact requirements listed above. Save yourself the headache and learn to
[use and love Nix](/documentation/why-nix/).

## Project Root

Reactivated relies on `BASE_DIR` to find files. Your `node_modules` and `package.json`
_must_ be inside your `BASE_DIR` and siblings of `manage.py`.

## Installation

Run `npm install reactivated` and `pip install reactivated` to download the required
packages. Make sure the versions of these packages always match. They are published at
the same time.

> **Warning**: Ensure your `package.json` file has a `name` field, otherwise the build
> process wil fail.

## Server Setup

In your Django settings, add `reactivated` to `INSTALLED_APPS`.

At the very top of your `settings.py` file, also add:

```python
import django_stubs_ext

django_stubs_ext.monkeypatch()
```

Configure your `STATIC_DIRS` to include a `static` folder inside `BASE_DIR`. Assuming
you have no other directories listed, you can just add this to your settings:

```python
STATICFILES_DIRS = (BASE_DIR / "static/",)
```

> **Warning**: If your current setup of static files includes a folder `dist`, you need
> to rename that folder. Vite's build process relies on the `dist` folder so Reactivated
> intercepts all requests for static content from that folder.

There is no custom template backend to add. Reactivated reads your stock
`DjangoTemplates` configuration: the context processors listed there become the typed
`Context` available to your React components. Your existing `TEMPLATES` setting works
as-is.

## Client Setup

Next to `manage.py` in `BASE_DIR`, create the following structure:

```
-   BASE_DIR
    -   manage.py
    -   package.json
    -   tsconfig.json
    -   client
        -   templates
```

Add the following code to `tsconfig.json`:

```json
{
    "extends": "reactivated/tsconfig.base.json",
    "include": ["./client/**/*"]
}
```

The base config sets strict mode, JSX, and the `@client` / `@reactivated` path
aliases. Generated code lands in `client/generated/`; add it to your `.gitignore`.

Notice there's no `client/index.tsx` in that structure. You don't need one: the
framework injects a default entry that boots everything. Create the file only when
you want to customize startup with `reactivate()`. See
[the entry point](/documentation/templates/#the-entry-point).

## Running it

Export a port and start the dev server:

```bash
export DEBUG_PORT=8000
reactivate
```

`python manage.py runserver` works too. [The Dev Server](/documentation/dev-server/)
covers what `reactivate` adds.

## Next steps

- Read the [concepts](/documentation/concepts/) and create your first
  [template](/documentation/templates/).
- Create a `client/components/Layout.tsx` component that your templates can reference.
- Then meet [picks](/documentation/picks/) and [RPC](/documentation/rpc/), which is
  where the framework earns its keep.
