from enum import Enum
from typing import Iterable, Tuple, Type, TypeVar, Any, TYPE_CHECKING

from django.db import models

from .constraints import EnumConstraint  # type: ignore[attr-defined]


def convert_enum_to_choices(enum: Type[Enum]) -> Iterable[Tuple[str, str]]:
    for member in enum:
        yield (member.name, member.value)


TEnum = TypeVar("TEnum", bound=Enum)
_ST = TypeVar("_ST", bound=Enum)
_GT = TypeVar("_GT", bound=Enum)


models.CharField.__class_getitem__ = classmethod(  # type: ignore[attr-defined]
    lambda cls, key: cls
)


class _EnumField(models.CharField[_ST, _GT]):  # , Generic[_ST, _GT]):
    def __init__(self, *, enum: Type[_GT], default: _GT):
        self.enum = enum
        choices = convert_enum_to_choices(enum)
        super().__init__(default=default, max_length=63, choices=choices)

    def deconstruct(self) -> Any:
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum"] = self.enum
        del kwargs["max_length"]
        del kwargs["choices"]
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, **kwargs):  # type: ignore[no-untyped-def]
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
            EnumConstraint(
                members=self.enum._member_names_,
                field_name=name,
                name=f"{cls._meta.db_table}_{name}_enum",
            )
        )

    """
    def from_db_value(
        self, value: Optional[str], expression: Any, connection: Any
    ) -> Optional[GT]:
        return self.convert_value_to_enum(value)

    def to_python(self, value: Union[GT, str, None]) -> Optional[GT]:
        if isinstance(value, self.enum):
            return value
        assert isinstance(value, str) or value is None
        return self.convert_value_to_enum(value)
    """


"""
if TYPE_CHECKING:
    Wrapper = EnumField

    def make_enum_field(enum: Type[TEnum], default: TEnum) -> Wrapper[TEnum, TEnum]:
        return cast(
            Wrapper[TEnum, TEnum],
            Wrapper(
                enum=enum, default=default,
            ),
        )
    EnumField = make_enum_field  # type: ignore[assignment]
"""

if TYPE_CHECKING:
    def EnumField(enum: Type[TEnum], default: TEnum) -> _EnumField[TEnum, TEnum]:
        return _EnumField[TEnum, TEnum](enum=enum, default=default)
else:
    class EnumField(_EnumField):
        pass
