from typing import Dict, cast

import pytest
from django import forms
from django.http import HttpRequest
from django.urls import reverse

from reactivated import Pick
from reactivated.rpc import FormGroup, create_rpc
from sample.server.apps.samples import models

urlpatterns = []


class SimpleForm(forms.Form):
    char_field = forms.CharField()


class SpecializedHttpRequest(HttpRequest):
    extra_property: bool


special_rpc = create_rpc(
    lambda request: cast(SpecializedHttpRequest, request)
    if request.user.is_authenticated
    else False
)

anonymous_rpc = create_rpc(lambda request: request)


@anonymous_rpc
def simple_form(request: HttpRequest, form: SimpleForm) -> bool:
    return True


urlpatterns.append(simple_form)


@pytest.mark.urls("tests.rpc")
def test_simple_form(client):
    url = reverse("rpc_simple_form")
    response = client.get(url)
    assert response.status_code == 405

    response = client.post(url)

    assert response.status_code == 400
    assert response.json() == {"char_field": ["This field is required."]}

    response = client.post(url, {"char_field": "content"})
    assert response.status_code == 200
    assert response.json() is True


@anonymous_rpc
def empty_form(request: HttpRequest, form: None) -> bool:
    return True


urlpatterns.append(empty_form)


@pytest.mark.urls("tests.rpc")
def test_empty_form(client):
    url = reverse("rpc_empty_form")

    response = client.get(url)
    assert response.status_code == 405

    response = client.post(url)

    assert response.status_code == 200
    assert response.json() is True


class FormOne(forms.Form):
    field = forms.CharField()


class FormTwo(forms.Form):
    another_field = forms.CharField()


class SimpleFormGroup(FormGroup):
    first: FormOne
    second: FormTwo


@anonymous_rpc
def form_group(request: HttpRequest, form: SimpleFormGroup) -> bool:
    return True


urlpatterns.append(form_group)


@pytest.mark.urls("tests.rpc")
def test_form_group(client):
    url = reverse("rpc_form_group")

    response = client.get(url)
    assert response.status_code == 405

    response = client.post(url, {})
    assert response.status_code == 400
    assert response.json() == {
        "first": {"field": ["This field is required."]},
        "second": {"another_field": ["This field is required."]},
    }

    response = client.post(
        url, {"first-field": "Hello", "second-another_field": "Goodbye"}
    )
    assert response.status_code == 200
    assert response.json() is True


@anonymous_rpc.context
def opera(request: HttpRequest, pk: int) -> models.Opera:
    return models.Opera(pk=pk, name="My Opera Context")


class OperaForm(forms.ModelForm[models.Opera]):
    class Meta:
        model = models.Opera
        fields = ["name"]


@opera.process
def update_opera(
    request: HttpRequest, opera: models.Opera, form: OperaForm
) -> Dict[str, str]:
    return {
        "from_context": opera.pk,
        "from_form": form.cleaned_data["name"],
    }


urlpatterns.append(update_opera)


@pytest.mark.urls("tests.rpc")
def test_context_model_form(client):
    url = reverse("rpc_update_opera", args=[923])

    response = client.get(url)
    assert response.status_code == 405

    response = client.post(url, {})
    assert response.status_code == 400

    response = client.post(url, {"name": "Hello"})
    assert response.status_code == 200
    assert response.json() == {
        "from_context": "923",
        "from_form": "Hello",
    }


@opera.process
def update_opera_with_no_form(
    request: HttpRequest, opera: models.Opera, form: None
) -> bool:
    return True


urlpatterns.append(update_opera_with_no_form)


@pytest.mark.urls("tests.rpc")
def test_update_opera_with_no_form(client):
    url = reverse("rpc_update_opera_with_no_form", args=[923])

    response = client.get(url)
    assert response.status_code == 405

    response = client.post(url)
    assert response.status_code == 200
    assert response.json() is True


OperaSchema = Pick[models.Opera, "id", "name"]


@opera.rpc
def opera_detail(request: HttpRequest, opera: models.Opera) -> OperaSchema:
    return opera


urlpatterns.append(opera_detail)


@pytest.mark.urls("tests.rpc")
def test_opera_detail(client):
    url = reverse("rpc_opera_detail", args=[923])
    expected = {
        "name": "My Opera Context",
        "id": 923,
    }

    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == expected

    response = client.post(url)
    assert response.status_code == 200
    assert response.json() == expected
