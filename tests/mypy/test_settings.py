"""Minimal Django settings for mypy plugin tests.

Uses sqlite3 so the tests don't require psycopg2 or a running database.
"""

SECRET_KEY = "test-secret-key"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
