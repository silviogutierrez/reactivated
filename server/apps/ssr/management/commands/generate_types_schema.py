from django.core.management.base import BaseCommand, CommandError

from typing import Any

from ... import generate_schema


class Command(BaseCommand):
    help = 'Generates a JSON schema for all registered types.'

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(generate_schema())
