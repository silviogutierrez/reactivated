from typing import Any

from django.core.management.base import BaseCommand

from ...apps import generate_schema, get_schema


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def handle(self, *args: Any, **options: Any) -> None:
        schema = get_schema()
        generate_schema(schema=schema, skip_cache=True)
