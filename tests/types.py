import pytest

from reactivated import create_schema
from reactivated.pick import get_field_descriptor
from typing import NamedTuple


class NamedTupleType(NamedTuple):
    first: str
    second: bool
    third: int


def test_generate_schema_for_type():
    definitions = {}
    create_schema(NamedTupleType, definitions)
    assert 1 == 1


from django.db import models as django_models
from sample.server.apps.samples import models


def test_get_field_descriptor():
    descriptor, path = get_field_descriptor(models.Opera, ['has_piano_transcription'])
    assert isinstance(descriptor, django_models.BooleanField)
    assert path == ()

    descriptor, path = get_field_descriptor(models.Opera, ['composer', 'name'])
    assert isinstance(descriptor, django_models.CharField)
    assert path == (('composer', False),)

    descriptor, path = get_field_descriptor(models.Opera, ['composer', 'countries', 'name'])
    assert isinstance(descriptor, django_models.CharField)
    assert path == (('composer', False), ('countries', True))

    descriptor, path = get_field_descriptor(models.Opera, ['composer', 'composer_countries', 'was_born'])
    assert isinstance(descriptor, django_models.BooleanField)
    assert path == (('composer', False), ('composer_countries', True))
