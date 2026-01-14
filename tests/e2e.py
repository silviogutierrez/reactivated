import json
import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest
from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse
from django.urls import path

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
    registry.rpc_registry.clear()

    call_command("generate_client_assets")
    call_command("build")

    # Debug: Get raw HTML before JS runs (using Django test client)
    raw_response = client.get("/")
    print(f"RAW HTML (no JS): {raw_response.content.decode()}")

    page.goto(live_server.url)
    content = page.content()
    print(f"PLAYWRIGHT CONTENT (after JS): {content}")

    # Check that CSS is loaded via preinit (data-precedence is added by React's preinit)
    assert 'href="/static/dist/index.css"' in content
    assert 'data-precedence="default"' in content

    # Fetch and verify CSS contains expected styles from vanilla-extract
    import requests

    css_response = requests.get(f"{live_server.url}/static/dist/index.css")
    assert css_response.status_code == 200
    css_content = css_response.text
    assert "max-width:" in css_content  # from layout style
    assert "color:" in css_content  # from multiple styles

    # Check that the page content is rendered
    assert "<h1>Hello World! It’s good to be here.</h1>" in content


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
    registry.rpc_registry.clear()

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


urlpatterns = [
    path("", lambda request: HttpResponse("ok")),
]


@pytest.mark.urls("tests.e2e")
def test_unnamed_urls(tmp_path):
    from sample.server.apps.samples.templates import HelloWorld

    registry.type_registry.clear()
    registry.global_types.clear()
    registry.global_types["Widget"] = registry.DefaultWidgetType
    registry.global_types["models"] = registry.DefaultModelsType
    registry.template_registry.clear()
    registry.interface_registry.clear()
    registry.value_registry.clear()
    registry.definitions_registry.clear()
    registry.rpc_registry.clear()

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
    registry.rpc_registry.clear()

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
