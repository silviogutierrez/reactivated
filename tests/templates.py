import pickle
from typing import Dict, NamedTuple, Optional

from reactivated import Pick, template
from sample.server.apps.samples import models


def test_serialization():
    @template
    class Test(NamedTuple):
        first: str
        second: bool

    context = Test(first="thing", second=True)
    response = context.render(None)
    assert response.context_data == context
    assert response.resolve_context(response.context_data) == {
        "first": "thing",
        "second": True,
    }


@template
class PickleTemplate(NamedTuple):
    first: str
    second: bool


def test_pickling():
    @template
    class Test(NamedTuple):
        first: str
        second: bool

    context = PickleTemplate(first="thing", second=True)
    response = context.render(None)
    # Force response to think its rendered
    response.content = b"bar"
    pickled = pickle.dumps(response)
    assert isinstance(pickled, bytes)
    assert pickle.loads(pickled).content == b"bar"


def test_union_with_pick():
    instance = models.Continent(name="Atlantis", hemisphere="Ocean")

    @template
    class Test(NamedTuple):
        union: Optional[Pick[models.Continent, "name"]]

    context = Test(union=instance)
    response = context.render(None)
    assert response.context_data == context
    assert response.resolve_context(response.context_data) == {
        "union": {"name": "Atlantis"}
    }


def test_non_class_based_members():
    @template
    class NonClass(NamedTuple):
        non_class_member: Dict[str, str]

    context = NonClass(non_class_member={"a": "b"})
    response = context.render(None)
    assert response.context_data == context
    assert response.resolve_context(response.context_data) == {
        "non_class_member": {"a": "b"}
    }
