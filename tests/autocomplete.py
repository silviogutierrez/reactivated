import pytest

from reactivated import forms
from sample.server.apps.samples import models


@pytest.mark.django_db
@pytest.mark.urls("tests.urls")
def test_autocomplete(client):
    composer = models.Composer.objects.create(name="Richard Wagner")
    models.Composer.objects.create(name="Wolfgang Amadeus Mozart")

    assert client.get("/autocomplete-view/").status_code == 200

    assert (
        client.post(
            "/autocomplete-view/",
            {"name": "Zarzuela", "style": "BUFFA", "composer": composer.pk},
        ).status_code
        == 302
    )

    response = client.get(
        "/autocomplete-view/", {"autocomplete": "name", "query": "Wagner"}
    )
    assert "Rendered form" in str(response.content)

    response = client.get(
        "/autocomplete-view/", {"autocomplete": "composer", "query": "Wagner"}
    )
    assert response.json()["results"][0]["label"] == "Richard Wagner"


@pytest.mark.django_db
@pytest.mark.urls("tests.urls")
def test_invalid_value(client):
    response = client.post(
        "/autocomplete-view/", {"name": "Zarzuela", "composer": "21s7"}
    )
    assert "Select a valid choice" in response.context["form"].errors["composer"][0]
    assert response.context["form"]["composer"].value() == "21s7"


@pytest.mark.django_db
@pytest.mark.urls("tests.urls")
def test_typed_autocomplete(client):
    composer = models.Composer.objects.create(name="Richard Wagner")
    models.Composer.objects.create(name="Wolfgang Amadeus Mozart")

    assert client.get("/typed-autocomplete-view/").status_code == 200

    assert (
        client.post(
            "/typed-autocomplete-view/", {"name": "Zarzuela", "composer": composer.pk}
        ).status_code
        == 302
    )

    response = client.get(
        "/typed-autocomplete-view/", {"autocomplete": "name", "query": "Wagner"}
    )
    assert "" in str(response.content)

    response = client.get(
        "/typed-autocomplete-view/", {"autocomplete": "composer", "query": "Wagner"}
    )
    assert response.json()["results"][0]["label"] == "Richard Wagner"


def test_prefix_calculation(client):
    assert forms.get_form_or_form_set_descriptor("opera_form_set-0-composer_field") == (
        "opera_form_set",
        "composer_field",
    )

    assert forms.get_form_or_form_set_descriptor("opera_form-composer_field") == (
        "opera_form",
        "composer_field",
    )

    assert forms.get_form_or_form_set_descriptor("composer_field") == (
        None,
        "composer_field",
    )
