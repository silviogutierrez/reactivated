from typing import Any

from django.core.management.base import BaseCommand

# from ... import generate_schema
from ...apps import generate_schema


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def handle(self, *args: Any, **options: Any) -> None:
        generate_schema(skip_cache=True)
