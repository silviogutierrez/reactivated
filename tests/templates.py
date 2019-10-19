from typing import Dict, NamedTuple, Optional

from reactivated import Pick, template
from sample.server.apps.samples import models


def test_serialization():
    @template
    class Test(NamedTuple):
        first: str
        second: bool

    assert Test(first="thing", second=True).render(None).context_data == {
        "first": "thing",
        "second": True,
    }


def test_union_with_pick():
    instance = models.Continent(name="Atlantis", hemisphere="Ocean")

    @template
    class Test(NamedTuple):
        union: Optional[Pick[models.Continent, "name"]]

    assert Test(union=instance).render(None).context_data == {
        "union": {"name": "Atlantis"}
    }


def test_non_class_based_members():
    @template
    class NonClass(NamedTuple):
        non_class_member: Dict[str, str]

    assert NonClass(non_class_member={"a": "b"}).render(None).context_data == {
        "non_class_member": {"a": "b"}
    }
