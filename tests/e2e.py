import os

from django.core.management import call_command
from django.urls import reverse


def test_end_to_end(client, live_server):
    os.chdir("sample")
    call_command("build")

    if os.path.exists("./node_modules/.bin/reactivated.sock"):
        os.remove("./node_modules/.bin/reactivated.sock")

    url = reverse("home_page")
    response = client.get(url)
    assert "<h1>Hello World!</h1>" in response.rendered_content
    os.chdir("../")
