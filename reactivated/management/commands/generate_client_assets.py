import argparse
from typing import Any

from django.core.management.base import BaseCommand

from ...apps import generate_schema, get_schema


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--cached",
            action="store_false",
            help="Use cached assets if they exist",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        skip_cache: bool = options.get("cached", True)

        schema = get_schema()
        generate_schema(schema=schema, skip_cache=skip_cache)
