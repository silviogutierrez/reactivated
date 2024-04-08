# Existing projects

Our [all-in-one setup script](/documentation/getting-started/) is the best way to use
Reactivated.

But at its core, Reactivated can be installed from **npm** and **PyPI** just like any
other packages.

## Requirements

-   Python 3.9
-   Node.js 18
-   PostgreSQL 10 or higher
-   Django 4.0

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

## Server Setup

In your Django settings, add `reactivated` to the _end_ of `INSTALLED_APPS`.

Configure your `STATIC_DIRS` to include a `static` folder inside `BASE_DIR`. Assuming
you have no other directories listed, you can just add this to your settings:

```python
STATICFILES_DIRS = (BASE_DIR / "static/",)
```

Now add the `JSX` template backend to your `TEMPLATES` setting. Assuming you want to
keep your regular Django templates as well, it would look something like this:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    {
        "BACKEND": "reactivated.backend.JSX",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csrf",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
            ]
        },
    },
]
```

## Client Setup

Next to `manage.py` in `BASE_DIR`, create the following structure:

```
-   BASE_DIR
    -   manage.py
    -   tsconfig.json
    -   client
        -   index.tsx
        -   templates
```

Add the following code to `tsconfig.json`:

```json
{
    "compilerOptions": {
        "strict": true,
        "sourceMap": true,
        "noEmit": true,
        "module": "esnext",
        "moduleResolution": "node",
        "target": "es2017",
        "esModuleInterop": true,
        "allowJs": true,
        "jsx": "react",
        "baseUrl": ".",
        "skipLibCheck": true,
        "paths": {
            "@client/*": ["client/*"],
            "@reactivated": ["node_modules/_reactivated"],
            "@reactivated/*": ["node_modules/_reactivated/*"]
        }
    },
    "include": ["./client/**/*"]
}
```

And the following code to `client/index.tsx`:

```typescript
import React from "react";
import {hydrate} from "react-dom";

import {Provider, getServerData, getTemplate} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

const {props, context} = getServerData();

const Template = getTemplate(context);

hydrate(
    <HelmetProvider>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </HelmetProvider>,
    document.getElementById("root"),
);
```

That completes the setup. You can now run `python manage.py runserver` to start coding.

## Next steps

-   Review the [API](/documentation/api/) and create your first `template`.
-   Create a `client/components/Layout.tsx` component that your templates can reference.
    Be sure to include links using `Helmet` to your bundled files.

    For your styles:  
    `` <link rel="stylesheet" type="text/css" href={`${context.STATIC_URL}dist/index.css`} /> ``  
    For your code:  
    `` <script defer crossOrigin="anonymous" src={`${context.STATIC_URL}dist/index.js`} /> ``.
