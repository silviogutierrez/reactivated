from typing import Any

from django.core.management.base import BaseCommand

import subprocess
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def handle(self, *args: Any, **options: Any) -> None:
        entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

        build_env = {
            **os.environ.copy(),
            "REACTIVATED_WATCH": "false",
        }

        client_process = subprocess.Popen(
            ["node", "./node_modules/reactivated/build.client.js", *entry_points],
            stdout=subprocess.PIPE,
            env=build_env,
        )
        server_process = subprocess.Popen(
            ["node", "./node_modules/reactivated/build.server.js", *entry_points],
            stdout=subprocess.PIPE,
            env=build_env,
        )
