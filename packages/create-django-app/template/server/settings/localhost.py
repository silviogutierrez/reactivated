from .common import *

ALLOWED_HOSTS = ["*"]

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# See: https://dizballanze.com/django-blazing-fast-tests/
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

INSTALLED_APPS += ["server.example", "reactivated"]

MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"] + MIDDLEWARE

TEMPLATES += [
    {
        "BACKEND": "reactivated.backend.JSX",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
            ]
        },
    },
]

STATICFILES_DIRS = (BASE_DIR / "static/",)

STATIC_ROOT = BASE_DIR / "collected/"

import dj_database_url

DATABASES["default"] = dj_database_url.config(default="postgres:///database")
