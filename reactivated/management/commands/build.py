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
        }

        tsc_process = subprocess.Popen(
            ["npm", "exec", "tsc", "--", "--noEmit"],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )
        client_process = subprocess.Popen(
            [
                "npm",
                "exec",
                "build.client.js",
                "--",
                *entry_points,
            ],
            stdout=subprocess.PIPE,
            env=build_env,
            cwd=settings.BASE_DIR,
        )
        renderer_process = subprocess.Popen(
            ["npm", "exec", "build.renderer.js"],
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
                        "npm",
                        "exec",
                        "terser",
                        "--",
                        f"{DIST_ROOT}{bundle}.js",
                        f"--source-map=content='{DIST_ROOT}{bundle}.js.map'",
                        "--compress",
                        "--mangle",
                        "-o",
                        f"{DIST_ROOT}{bundle}.js",
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
                    "npm",
                    "exec",
                    "sentry-cli",
                    "--",
                    "releases",
                    "files",
                    os.environ["TAG_VERSION"],
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
