# type: ignore
from django.db import models

from .constraints import EnumConstraint


class EnumField(models.CharField):
    def __init__(self, *, enum, default):
        self.enum = enum
        super().__init__(default=default, max_length=63)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum"] = self.enum
        del kwargs['max_length']
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, **kwargs):
        """
        We don't store the enum in the constraint. Instead, we store the fields
        so the autodetection for changed enums works automatically.
        """
        super().contribute_to_class(cls, name, **kwargs)
        if "constraints" not in cls._meta.original_attrs:
            cls._meta.original_attrs["constraints"] = []

        cls._meta.constraints.append(
            EnumConstraint(members=self.enum._member_names_, field_name=name, name=f"%(app_label)s_%(class)s_{name}_enum")
        )
