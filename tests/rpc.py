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


urlpatterns = [
    simple_form,
]


@pytest.mark.urls("tests.rpc")
def test_(client):
    url = reverse("rpc_simple_form")
    response = client.post(url)

    assert response.status_code == 400
    assert response.json() == {"char_field": ["This field is required."]}

    response = client.post(url, {"char_field": "content"})
    assert response.status_code == 200
    assert response.json() is True
