import pytest

from reactivated import create_schema
from typing import NamedTuple


class NamedTupleType(NamedTuple):
    first: str
    second: bool
    third: int


def test_generate_schema_for_type(client):
    definitions = {}
    create_schema(NamedTupleType, definitions)
    assert False
