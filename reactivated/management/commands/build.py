import os
import subprocess
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DIST_ROOT = "static/dist/"


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--upload-sourcemaps",
            action="store_true",
            help="Upload sourcemaps to Sentry",
        )
        parser.add_argument(
            "--no-minify",
            action="store_true",
            help="Skip minifying using terser to speed up build.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

        build_env = {
            **os.environ.copy(),
            "NODE_ENV": "production",
            "BASE": f"{settings.STATIC_URL}dist/",
        }

        tsc_process = subprocess.Popen(
            ["npm", "exec", "tsc", "--", "--noEmit"],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )

        tsc_output, tsc_error = tsc_process.communicate()

        if tsc_process.returncode != 0:
            raise CommandError("TypeScript error. Run 'tsc --noEmit' manually.")

        client_process = subprocess.Popen(
            [
                "npm",
                "exec",
                "build.client",
                "--",
                *entry_points,
            ],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )

        client_output, client_error = client_process.communicate()

        if client_output == b"":
            # Sometimes Popen / npm exec fail silently with return code 0. I
            # think race conditions between multiple processes all calling npm
            # exec, so the communicate() has to be in between. every process.
            raise CommandError("Problems spawning process, this should not ever happen")

        if client_process.returncode != 0:
            raise CommandError("vite errors")

        if options["upload_sourcemaps"] is True:
            assert "RELEASE_VERSION" in os.environ, "RELEASE_VERSION must be set"

            sentry_process = subprocess.Popen(
                [
                    "npm",
                    "exec",
                    "sentry-cli",
                    "--",
                    "releases",
                    "files",
                    os.environ["RELEASE_VERSION"],
                    "upload-sourcemaps",
                    DIST_ROOT,
                    "--url-prefix",
                    "~/static/dist",
                ],
                stdout=subprocess.PIPE,
                env=build_env,
                cwd=settings.BASE_DIR,
            )
            sentry_output, sentry_error = sentry_process.communicate()
