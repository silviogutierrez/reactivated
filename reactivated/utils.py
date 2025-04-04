from __future__ import annotations

import collections.abc
import inspect
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Manager
from django.utils.functional import Promise

if TYPE_CHECKING:
    from reactivated.backend import JSX


# Mock is_simple_callable for now
# instead of the more sophisticated one from rest_framework.fields
def is_simple_callable(possible_callable: Any) -> bool:
    return callable(possible_callable)


# From Django Rest Framework 3.6
def get_attribute(instance: Any, attrs: Sequence[str]) -> Any:
    """
    Similar to Python's built in `getattr(instance, attr)`,
    but takes a list of nested attributes, instead of a single attribute.
    Also accepts either attribute lookup on objects or dictionary lookups.
    """
    for attr in attrs:
        if instance is None:
            # Break out early if we get `None` at any point in a nested lookup.
            return None
        try:
            if isinstance(instance, collections.abc.Mapping):
                instance = instance[attr]
            else:
                instance = getattr(instance, attr)
        except ObjectDoesNotExist:
            return None

        if isinstance(instance, Manager):
            instance = instance.all()
        elif is_simple_callable(instance):
            try:
                instance = instance()
            except (AttributeError, KeyError) as exc:
                # If we raised an Attribute or KeyError here it'd get treated
                # as an omitted field in `Field.get_attribute()`. Instead we
                # raise a ValueError to ensure the exception is not masked.
                raise ValueError(
                    'Exception raised in callable attribute "{}"; original exception was: {}'.format(
                        attr, exc
                    )
                )

    return instance


# From https://github.com/encode/django-rest-framework/blob/master/rest_framework/utils/field_mapping.py
class ClassLookupDict:
    """
    Takes a dictionary with classes as keys.
    Lookups against this object will traverses the object's inheritance
    hierarchy in method resolution order, and returns the first matching value
    from the dictionary or raises a KeyError if nothing matches.
    """

    def __init__(self, mapping: Any) -> None:
        self.mapping = mapping

    def __getitem__(self, key: Any) -> Any:
        base_class = key

        # Handle lazy translated strings, as could come from say labels,
        # verbose names, etc.

        # Useful when a Union is typed as Union[str, somethingelse] but
        # actually receives a proxy at runtime.
        if issubclass(base_class, Promise):
            if getattr(base_class, "_delegate_text", False):
                base_class = str
            # Detect a string, hacky.
            elif getattr(base_class, "rpartition", False):
                base_class = str
            else:
                assert (
                    False
                ), "Unsupported proxy / lazy promise type. See django/utils/functional.py"

        # DRF uses this, we do not.
        # if hasattr(key, "_proxy_class"):
        #     # Deal with proxy classes. Ie. BoundField behaves as if it
        #     # is a Field instance when using ClassLookupDict.
        #     base_class = key._proxy_class
        # else:
        #     base_class = key.__class__

        for cls in inspect.getmro(base_class):
            if cls in self.mapping:
                return self.mapping[cls]
        raise KeyError("Class %s not found in lookup." % base_class.__name__)

    def __setitem__(self, key: Any, value: Any) -> Any:
        self.mapping[key] = value


def get_template_engine() -> JSX:
    from django.template import engines

    from reactivated.backend import JSX

    for engine in engines.all():
        if isinstance(engine, JSX):
            return engine
    assert False, "JSX engine not found in settings.TEMPLATES"
