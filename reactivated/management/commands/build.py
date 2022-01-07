import os
import subprocess
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def handle(self, *args: Any, **options: Any) -> None:
        entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

        build_env = {
            **os.environ.copy(),
            "NODE_ENV": "production",
        }

        tsc_process = subprocess.Popen(
            ["./node_modules/.bin/tsc", "--noEmit"],
            stdout=subprocess.PIPE,
            env=build_env,
        )
        client_process = subprocess.Popen(
            ["node", "./node_modules/reactivated/build.client.js", *entry_points],
            stdout=subprocess.PIPE,
            env=build_env,
        )
        renderer_process = subprocess.Popen(
            ["node", "./node_modules/reactivated/build.renderer.js"],
            stdout=subprocess.PIPE,
            env=build_env,
        )

        tsc_output, tsc_error = tsc_process.communicate()
        client_output, client_error = client_process.communicate()
        renderer_ouput, renderer_error = renderer_process.communicate()

        if tsc_process.returncode != 0:
            raise CommandError("TypeScript error. Run 'tsc --noEmit' manually.")

        if client_error.returncode != 0  or renderer_error.returncode != 0:
            raise CommandError("esbuild errors")
