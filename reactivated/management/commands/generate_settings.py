from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from typing import Any

from ... import generate_settings


class Command(BaseCommand):
    help = 'Generates a JSON representation of all settings.'

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(generate_settings())
