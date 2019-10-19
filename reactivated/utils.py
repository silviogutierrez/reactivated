import collections
from typing import Any, Sequence

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Manager


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
