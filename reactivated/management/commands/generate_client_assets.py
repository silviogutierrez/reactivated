import argparse
from typing import Any

from django.core.management.base import BaseCommand

from ... import run_generations


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
        run_generations(skip_cache)
