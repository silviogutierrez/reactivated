from __future__ import annotations

import collections
import inspect
from typing import TYPE_CHECKING, Any, Sequence

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Manager

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
            if isinstance(instance, collections.Mapping):
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
                    'Exception raised in callable attribute "{0}"; original exception was: {1}'.format(
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
