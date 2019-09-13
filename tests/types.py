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


from sample.server.apps.samples import models


def test_get_field_descriptor():
    descriptor = get_field_descriptor(models.Opera, ['composer', 'name'])
    breakpoint()
