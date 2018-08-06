from django.http import HttpRequest

from typing import Callable

success: Callable[[HttpRequest, str], None]
error: Callable[[HttpRequest, str], None]
