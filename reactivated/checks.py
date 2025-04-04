from typing import Any

from django.conf import settings
from django.core.checks import Error, register


@register()
def check_installed_app_order(app_configs: Any, **kwargs: Any) -> list[Error]:
    if False and settings.INSTALLED_APPS[-1] != "reactivated":
        return [
            Error(
                "reactivated must be last in INSTALLED_APPS",
                obj=settings,
                id="reactivated.E001",
            )
        ]

    return []
