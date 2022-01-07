import os
import subprocess
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def handle(self, *args: Any, **options: Any) -> None:
        entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

        build_env = {
            **os.environ.copy(),
            "NODE_ENV": "production",
        }

        client_process = subprocess.Popen(
            ["node", "./node_modules/reactivated/build.client.js", *entry_points],
            stdout=subprocess.PIPE,
            env=build_env,
        )
        client_process.wait()
        server_process = subprocess.Popen(
            ["node", "./node_modules/reactivated/build.server.js"],
            stdout=subprocess.PIPE,
            env=build_env,
        )
        client_output, client_error = client_process.communicate()
        server_output, server_error = server_process.communicate()
