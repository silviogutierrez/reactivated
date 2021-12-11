from typing import Any

from django.core.management.base import BaseCommand

from ...apps import get_schema


class Command(BaseCommand):
    help = "Print the JSON schema for all client assets"

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(get_schema())
