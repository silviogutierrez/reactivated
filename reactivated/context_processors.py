from typing import TypedDict
from urllib.parse import urljoin, urlparse, urlunparse

from django.apps import apps
from django.conf import settings
from django.http import HttpRequest

from .apps import ReactivatedConfig


class ReactivatedStaticProcessor(TypedDict):
    STATIC_URL: str
    BUNDLE_URL: str


def static(request: HttpRequest) -> ReactivatedStaticProcessor:
    """
    Add static-related context variables to the context.
    """
    app_config = apps.get_app_config(ReactivatedConfig.name)

    bundle_subdir = getattr(settings, "REACTIVATED_STATIC_DIR", "dist/")
    bundle_url = urljoin(settings.STATIC_URL, bundle_subdir)
    if False and app_config.esbuild_port:
        parts = urlparse(f"{request.scheme}://{request.get_host()}/")
        parts = parts._replace(netloc=f"{parts.hostname}:{app_config.esbuild_port}")
        bundle_url = urlunparse(parts)
    return ReactivatedStaticProcessor(
        STATIC_URL=settings.STATIC_URL,
        BUNDLE_URL=bundle_url,
    )
