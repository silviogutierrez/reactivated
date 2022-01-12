import os

from django.core.management import call_command

from reactivated import registry

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def test_end_to_end(client, live_server, page):
    registry.type_registry.clear()
    registry.global_types.clear()
    registry.template_registry.clear()
    registry.value_registry.clear()
    registry.definitions_registry.clear()

    os.chdir("sample")
    call_command("generate_client_assets")
    call_command("build")

    if os.path.exists("./node_modules/.bin/reactivated.sock"):
        os.remove("./node_modules/.bin/reactivated.sock")

    page.goto(live_server.url)
    assert "<h1>Hello World!</h1>" in page.content()
    os.chdir("../")
