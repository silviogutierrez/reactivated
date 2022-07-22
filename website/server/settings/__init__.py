from .common import *  # noqa: F401

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# See: https://dizballanze.com/django-blazing-fast-tests/
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
