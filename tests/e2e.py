import os

import pytest
import requests
from django.core.management import call_command
from playwright.async_api import Page

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.mark.asyncio
async def test_end_to_end(client, live_server, page: Page):
    call_command("generate_client_assets")
    call_command("build")

    # Debug: Get raw HTML before JS runs (using Django test client)
    raw_response = client.get("/")
    print(f"RAW HTML (no JS): {raw_response.content.decode()}")

    await page.goto(live_server.url)
    content = await page.content()
    print(f"PLAYWRIGHT CONTENT (after JS): {content}")

    # Check that CSS is loaded via preinit (data-precedence is added by React's preinit)
    assert 'href="/static/dist/index.css?v=' in content
    assert 'data-precedence="default"' in content

    # Fetch and verify CSS contains expected styles from tailwind
    css_response = requests.get(f"{live_server.url}/static/dist/index.css")
    assert css_response.status_code == 200
    css_content = css_response.text
    assert "max-width:" in css_content  # from layout style
    assert "color:" in css_content  # from multiple styles

    # Check that the page content is rendered
    assert "<h1>Hello World! It's good to be here.</h1>" in content
