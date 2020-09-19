# type: ignore
from django.db import models
from typing import Iterable, Tuple, Type

from enum import Enum

from .constraints import EnumConstraint


def convert_enum_to_choices(enum: Type[Enum]) -> Iterable[Tuple[str, str]]:
    for member in enum:
        yield (member.name, member.value)


class EnumField(models.CharField):
    def __init__(self, *, enum: Type[Enum], default):
        self.enum = enum
        choices = convert_enum_to_choices(enum)
        super().__init__(default=default.name, max_length=63, choices=choices)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum"] = self.enum
        del kwargs['max_length']
        del kwargs['choices']
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, **kwargs):
        """
        We don't store the enum in the constraint. Instead, we store the fields
        so the autodetection for changed enums works automatically.
        """
        super().contribute_to_class(cls, name, **kwargs)
        if "constraints" not in cls._meta.original_attrs:
            cls._meta.original_attrs["constraints"] = []

        # Note that we cannot use the constraint name interpolation syntax
        # because it's too late at this point. It's the metaclass that actually
        # interpolates the values.
        #
        # Fortunately, we can create a name dynamically.
        cls._meta.constraints.append(
            EnumConstraint(members=self.enum._member_names_, field_name=name, name=f"{cls._meta.db_table}_{name}_enum")
        )

        class RemoteField:
            model = cls

        class FakeString(str):
            pass

        # cls._meta.model_name = FakeString(cls._meta.model_name)
        # self.remote_field = RemoteField()
