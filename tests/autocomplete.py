import pytest

from server.apps.samples import models


@pytest.mark.django_db
@pytest.mark.urls("tests.urls")
def test_autocomplete(client):
    models.Composer.objects.create(name="Richard Wagner")
    models.Composer.objects.create(name="Wolfgang Amadeus Mozart")
    response = client.get("/autocomplete-view/", {"autocomplete": "composer", "query": "Wagner"})
    assert response.json()['results'][0]['label'] == "Richard Wagner"



from typing import NamedTuple

class FormOrFormSet(NamedTuple):
    prefix: str
    name: str

def get_form_or_form_set_descriptor(field_name: str) -> FormOrFormSet:
    FORM_SET_REGEX = "(.*)?(-[0-9]-)(.*)"
    FORM_REGEX = "(.*)?(-[0-9]-)(.*)"


def test_prefix_calculation(client):
    import re
    FORM_SET_REGEX = "(.*)?(-[0-9]-)(.*)"

    assert re.match(FORM_SET_REGEX, "opera_form_set-0-composer_field").groups() == ('opera_form_set', '-0-', 'composer_field')
    assert re.match(FORM_SET_REGEX, "opera_form_set-0-0-composer_field").groups() == ('opera_form_set-0', '-0-', 'composer_field')
    assert re.match(FORM_SET_REGEX, "opera_form_set-name") is None
    assert re.match(FORM_SET_REGEX, "name") is None
    return 
    # assert re.match(FORM_SET_REGEX, "opera_form_set-0-0-composer-field") is not None

    # assert re.split(REGEX, "opera_form_set-0-composer-field") == ["opera_form_set", "composer-field"]
    foo = re.match(REGEX, "opera_form_set-0-composer-field")
    foo = re.match(REGEX, "opera_form-name")
    # foo = re.match(REGEX, "name")
    # foo = re.match(REGEX, "opera-form-set-0-0-composer-field") # == ["opera_form_set", "composer-field"]
    breakpoint()
