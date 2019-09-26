from typing import Any

from django.core.management.base import BaseCommand

# from ... import generate_schema
from ...apps import get_schema


class Command(BaseCommand):
    help = "Generates a JSON schema for all registered types."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(get_schema())
