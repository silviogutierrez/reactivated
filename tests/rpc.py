import pytest
from django import forms
from django.http import HttpRequest
from django.urls import reverse

from reactivated.rpc import create_rpc


class SimpleForm(forms.Form):
    char_field = forms.CharField()


class SpecializedHttpRequest(HttpRequest):
    extra_property: bool


special_rpc = create_rpc(
    lambda request: cast(SpecializedHttpRequest, request)
    if request.is_authenticated
    else False
)

anonymous_rpc = create_rpc(lambda request: request)


@anonymous_rpc
def simple_form(request: HttpRequest, form: SimpleForm) -> bool:
    return True


@anonymous_rpc
def empty_form(request: HttpRequest, form: None) -> bool:
    return True


urlpatterns = [
    simple_form,
    empty_form,
]


@pytest.mark.urls("tests.rpc")
def test_simple_form(client):
    url = reverse("rpc_simple_form")
    response = client.post(url)

    assert response.status_code == 400
    assert response.json() == {"char_field": ["This field is required."]}

    response = client.post(url, {"char_field": "content"})
    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.urls("tests.rpc")
def test_empty_form(client):
    url = reverse("rpc_empty_form")

    response = client.get(url)
    assert response.status_code == 405

    response = client.post(url)

    assert response.status_code == 200
    assert response.json() is True
