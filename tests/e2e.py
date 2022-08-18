import json
import os
import subprocess
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import call_command

from reactivated import registry

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def test_end_to_end(client, live_server, page):
    registry.type_registry.clear()
    registry.global_types.clear()
    registry.global_types["Widget"] = registry.DefaultWidgetType
    registry.global_types["models"] = registry.DefaultModelsType
    registry.template_registry.clear()
    registry.interface_registry.clear()
    registry.value_registry.clear()
    registry.definitions_registry.clear()

    call_command("generate_client_assets")
    call_command("build")

    page.goto(live_server.url)
    assert "<h1>Hello World!</h1>" in page.content()


def test_default_widget(tmp_path):
    from sample.server.apps.samples.templates import HelloWorld

    registry.type_registry.clear()
    registry.global_types.clear()
    registry.global_types["Widget"] = registry.DefaultWidgetType
    registry.global_types["models"] = registry.DefaultModelsType
    registry.template_registry.clear()
    registry.interface_registry.clear()
    registry.value_registry.clear()
    registry.definitions_registry.clear()

    tsconfig = Path(settings.BASE_DIR) / "tsconfig.pytest.json"
    tsconfig.write_text(
        json.dumps(
            {
                "extends": "./tsconfig.json",
                "include": [
                    "./client/templates/HelloWorld.tsx",
                ],
            }
        )
    )

    with mock.patch(
        "reactivated.apps.get_urls_schema",
        return_value={
            "foo": {
                "route": "/foo/",
                "args": {},
            },
            "bar": {
                "route": "/bar/",
                "args": {"arg": "string"},
            },
        },
    ):
        HelloWorld.register()
        call_command("generate_client_assets")
        assert registry.global_types["Widget"] is registry.DefaultWidgetType
        tsc_process = subprocess.Popen(
            [
                "npm",
                "exec",
                "tsc",
                "--",
                "--noEmit",
                "--project",
                tsconfig,
            ],
            stdout=subprocess.PIPE,
            cwd=settings.BASE_DIR,
        )
        tsc_output, tsc_error = tsc_process.communicate()
        assert tsc_process.returncode == 0
    tsconfig.unlink()


def test_no_urls(tmp_path):
    from sample.server.apps.samples.templates import HelloWorld

    registry.type_registry.clear()
    registry.global_types.clear()
    registry.global_types["Widget"] = registry.DefaultWidgetType
    registry.global_types["models"] = registry.DefaultModelsType
    registry.template_registry.clear()
    registry.interface_registry.clear()
    registry.value_registry.clear()
    registry.definitions_registry.clear()

    tsconfig = Path(settings.BASE_DIR) / "tsconfig.pytest.json"
    tsconfig.write_text(
        json.dumps(
            {
                "extends": "./tsconfig.json",
                "include": [
                    "./client/templates/HelloWorld.tsx",
                ],
            }
        )
    )

    with mock.patch(
        "reactivated.apps.get_urls_schema",
        return_value={},
    ):
        HelloWorld.register()
        call_command("generate_client_assets")
        assert registry.global_types["Widget"] is registry.DefaultWidgetType
        tsc_process = subprocess.Popen(
            [
                "npm",
                "exec",
                "tsc",
                "--",
                "--noEmit",
                "--project",
                tsconfig,
            ],
            stdout=subprocess.PIPE,
            cwd=settings.BASE_DIR,
        )
        tsc_output, tsc_error = tsc_process.communicate()
        assert tsc_process.returncode == 0
    tsconfig.unlink()
