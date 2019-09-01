import pytest

from server.apps.samples import models


@pytest.mark.django_db
@pytest.mark.urls("tests.urls")
def test_autocomplete(client):
    models.Composer.objects.create(name="Richard Wagner")
    models.Composer.objects.create(name="Wolfgang Amadeus Mozart")
    response = client.get("/autocomplete-view/", {"autocomplete": "composer", "query": "Wagner"})
    assert response.json()['results'][0]['label'] == "Richard Wagner"
