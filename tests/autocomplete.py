import pytest

from server.apps.samples import models
from reactivated import forms


@pytest.mark.django_db
@pytest.mark.urls("tests.urls")
def test_autocomplete(client):
    models.Composer.objects.create(name="Richard Wagner")
    models.Composer.objects.create(name="Wolfgang Amadeus Mozart")
    response = client.get(
        "/autocomplete-view/", {"autocomplete": "composer", "query": "Wagner"}
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
