import os
import subprocess
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Generates all types and other client assets"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--upload-sourcemaps",
            action="store_true",
            help="Upload sourcemaps to Sentry",
        )
        parser.add_argument(
            "--no-minify", action="store_true", help="Minify using terser. Slow.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        entry_points = getattr(settings, "REACTIVATED_BUNDLES", ["index"])

        build_env = {
            **os.environ.copy(),
            "NODE_ENV": "production",
        }

        tsc_process = subprocess.Popen(
            [f"{settings.BASE_DIR}/node_modules/.bin/tsc", "--noEmit"],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )
        client_process = subprocess.Popen(
            [
                "node",
                f"{settings.BASE_DIR}/node_modules/reactivated/build.client.js",
                *entry_points,
            ],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )
        renderer_process = subprocess.Popen(
            ["node", f"{settings.BASE_DIR}/node_modules/reactivated/build.renderer.js"],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )

        tsc_output, tsc_error = tsc_process.communicate()
        client_output, client_error = client_process.communicate()
        renderer_ouput, renderer_error = renderer_process.communicate()

        if tsc_process.returncode != 0:
            raise CommandError("TypeScript error. Run 'tsc --noEmit' manually.")

        if client_process.returncode != 0 or renderer_process.returncode != 0:
            raise CommandError("esbuild errors")

        if options["no_minify"] is False:
            for bundle in entry_points:
                terser_process = subprocess.Popen(
                    [
                        "yarn",
                        "terser",
                        f"static/dist/{bundle}.js",
                        f"--source-map=content=static/dist/{bundle}.js.map",
                        "--compress",
                        "--mangle",
                        "-o",
                        f"static/dist/{bundle}.js",
                    ],
                    stdout=subprocess.PIPE,
                    env=build_env,
                    cwd=settings.BASE_DIR,
                )
                terser_process.communicate()

        if options["upload_sourcemaps"] is True:
            assert "TAG_VERSION" in os.environ, "TAG_VERSION must be set"

            sentry_process = subprocess.Popen(
                [
                    f"{settings.BASE_DIR}/node_modules/.bin/sentry-cli",
                    "releases",
                    "files",
                    os.environ["TAG_VERSION"],
                    "upload-sourcemaps",
                    "static/dist/",
                    "--url-prefix",
                    "~/static/dist",
                ],
                stdout=subprocess.PIPE,
                env=build_env,
                cwd=settings.BASE_DIR,
            )
            sentry_output, sentry_error = sentry_process.communicate()
