import json

from django.test import RequestFactory

from reactivated.renderer import get_accept_list, render_jsx_to_string


def test_get_accept_list():
    request_factory = RequestFactory(
        HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"
    )
    request = request_factory.get("/")
    accepts = get_accept_list(request)
    assert accepts == [
        "text/html",
        "application/xhtml+xml",
        "application/xml;q=0.9",
        "image/webp",
        "image/apng",
        "*/*;q=0.8",
        "application/signed-exchange;v=b3",
    ]


def test_render_to_json():
    request_factory = RequestFactory(HTTP_ACCEPT="application/json")
    request = request_factory.get("/")
    response = render_jsx_to_string(
        request,
        {"template_name": "doesnotmatter.tsx", "some": "property"},
        {"another": "property"},
    )
    assert json.loads(response) == {
        "context": {"some": "property", "template_name": "doesnotmatter.tsx"},
        "props": {"another": "property"},
    }
