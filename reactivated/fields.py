from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from django.core.exceptions import ValidationError
from django.db import DatabaseError, models
from django.db.models.fields import NOT_PROVIDED

from .constraints import EnumConstraint

if TYPE_CHECKING:
    from django.db.models.fields import _ValidatorCallable, _ErrorMessagesToOverride
else:

    class _ValidatorCallable:
        pass

    class _ErrorMessagesToOverride:
        pass


TEnum = TypeVar("TEnum", bound=Enum)
_ST = TypeVar("_ST", bound=Enum)
_GT = TypeVar("_GT", bound=Enum)


class EnumChoice(Generic[_GT]):
    def __init__(self, choice: _GT) -> None:
        self.choice = choice

    def __str__(self) -> str:
        return self.choice.name

    def __hash__(self) -> int:
        """
        Used by DRF when creating choices in `rest_framework/fields.py`
        """
        return hash((self.choice))

    def __eq__(self, other: Union[_GT, Any, str]) -> bool:
        if isinstance(other, str):
            return str(self.choice) == other
        elif isinstance(other, Enum):
            return self.choice == other
        return False


def convert_enum_to_choices(enum: Type[Enum]) -> Iterable[Tuple[EnumChoice[Enum], str]]:
    for member in enum:
        yield (EnumChoice(member), str(member.value))


class EnumChoiceIterator(Generic[_GT]):
    """ This is a special iterator that preserves the original enum. Useful so
    we can use the "choices" argument that triggers special Django behaviors,
    but leave our enum intact for reference."""

    def __init__(self, enum: Type[_GT]) -> None:
        self.enum = enum

    def __iter__(self) -> Any:
        return convert_enum_to_choices(self.enum)


def coerce_to_enum(
    enum: Type[_GT], value: Union[_GT, EnumChoice[_GT], str, None]
) -> Optional[_GT]:
    if isinstance(value, EnumChoice):
        return value.choice
    elif isinstance(value, enum):
        return value
    # Narrow the type
    assert isinstance(value, str) or value is None
    return parse_enum(enum, value)


models.CharField.__class_getitem__ = classmethod(  # type: ignore[attr-defined]
    lambda cls, key: cls
)


def parse_enum(enum: Type[_GT], value: Optional[str]) -> Optional[_GT]:
    if value is None:
        return None

    for member in enum:
        # Disabled form fields will come in as Enum.Member string
        # representations. So we handle both naked member names and the full
        # representation.
        #
        # See https://code.djangoproject.com/ticket/18431 and
        # TypedChoiceField's to_python call chain.
        if member.name == value or value == str(member):
            return member

    raise ValidationError(f"Invalid input for {enum}")


class _EnumField(models.CharField[_ST, _GT]):  # , Generic[_ST, _GT]):
    # So null is handled in when adding fields through migrations.
    empty_strings_allowed = False

    def __init__(
        self,
        *,
        enum: Type[_GT],
        default: Union[Type[NOT_PROVIDED], _GT, None] = NOT_PROVIDED,
        null: bool = False,
        verbose_name: Optional[Union[str, bytes]] = None,
        unique: bool = False,
        blank: bool = False,
        db_index: bool = False,
        editable: bool = True,
        help_text: str = "",
        db_column: Optional[str] = None,
        db_tablespace: Optional[str] = None,
        validators: Iterable[_ValidatorCallable] = (),
        error_messages: Optional[_ErrorMessagesToOverride] = None,
    ):
        self.enum = enum
        self.choices = EnumChoiceIterator(enum=enum)

        # We skip the constructor for CharField because we do *not* want
        # MaxLengthValidator added, as our enum members do not support __len__.
        models.Field.__init__(
            self,
            choices=self.choices,
            max_length=63,
            default=default,
            null=null,
            verbose_name=verbose_name,
            unique=unique,
            blank=blank,
            db_index=db_index,
            editable=editable,
            help_text=help_text,
            db_column=db_column,
            db_tablespace=db_tablespace,
            validators=validators,
            error_messages=error_messages,
        )

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
                members=self.enum._member_names_,  # type: ignore[arg-type]
                field_name=name,
                name=f"{cls._meta.db_table}_{name}_enum",
            )
        )

    def db_type(self, connection: Any) -> str:
        if connection.settings_dict["ENGINE"] != "django.db.backends.postgresql":
            raise DatabaseError("EnumField is only supported on PostgreSQL")
        return super().db_type(connection)

    def from_db_value(
        self, value: Optional[str], expression: Any, connection: Any
    ) -> Optional[_GT]:
        return parse_enum(self.enum, value)

    def to_python(self, value: Union[_GT, EnumChoice[_GT], str, None]) -> Optional[_GT]:
        return coerce_to_enum(self.enum, value)

    def get_prep_value(self, value: Union[_GT, str, None]) -> Optional[str]:
        member = self.to_python(value)
        if member is None:
            return None

        return str(member.name)

    def value_to_string(self, obj: Any) -> Optional[str]:
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs: Any) -> Any:
        from .forms import EnumChoiceField

        # We need to pass our own choice iterator otherwise list() is called upon
        # our choices by super().formfield and we lose the enum.
        defaults = {
            **kwargs,
            "choices_form_class": EnumChoiceField,
            "choices": self.choices,
        }
        return super().formfield(**defaults)


if TYPE_CHECKING:

    @overload
    def EnumField(  # type: ignore[misc]
        enum: Type[TEnum],
        default: Union[Type[NOT_PROVIDED], TEnum, None] = NOT_PROVIDED,
        null: Literal[False] = False,
        verbose_name: Optional[Union[str, bytes]] = None,
        unique: bool = False,
        blank: bool = False,
        db_index: bool = False,
        editable: bool = True,
        help_text: str = "",
        db_column: Optional[str] = None,
        db_tablespace: Optional[str] = None,
        validators: Iterable[_ValidatorCallable] = (),
        error_messages: Optional[_ErrorMessagesToOverride] = None,
    ) -> _EnumField[TEnum, TEnum]:
        ...

    @overload
    def EnumField(
        enum: Type[TEnum],
        default: Union[Type[NOT_PROVIDED], TEnum, None] = NOT_PROVIDED,
        null: Literal[True] = True,
        verbose_name: Optional[Union[str, bytes]] = None,
        unique: bool = False,
        blank: bool = False,
        db_index: bool = False,
        editable: bool = True,
        help_text: str = "",
        db_column: Optional[str] = None,
        db_tablespace: Optional[str] = None,
        validators: Iterable[_ValidatorCallable] = (),
        error_messages: Optional[_ErrorMessagesToOverride] = None,
    ) -> _EnumField[Optional[TEnum], Optional[TEnum]]:  # type: ignore[type-var]
        ...

    def EnumField(
        enum: Type[TEnum],
        default: Union[Type[NOT_PROVIDED], TEnum, None] = NOT_PROVIDED,
        null: Literal[True, False] = False,
        verbose_name: Optional[Union[str, bytes]] = None,
        unique: bool = False,
        blank: bool = False,
        db_index: bool = False,
        editable: bool = True,
        help_text: str = "",
        db_column: Optional[str] = None,
        db_tablespace: Optional[str] = None,
        validators: Iterable[_ValidatorCallable] = (),
        error_messages: Optional[_ErrorMessagesToOverride] = None,
    ) -> Union[_EnumField[TEnum, TEnum], _EnumField[Optional[TEnum], Optional[TEnum]]]:  # type: ignore[type-var]
        return _EnumField[TEnum, TEnum](enum=enum, default=default, null=null)


else:

    class EnumField(_EnumField):
        pass

    try:
        # DRF cannot serialize enums. So we do it by monkey patching. In the
        # future this may be a setting.

        # Any field with choices gets coerced by DRF to a ChoiceField,
        # regardless of its base type. So we have a special choice field to
        # look out for that.  Separately: read only fields, such as those set
        # to editable=False, will need to be mapped as well.
        from rest_framework import serializers

        class DRFEnumChoiceField(serializers.ChoiceField):
            def to_internal_value(self, data):
                data = super().to_internal_value(data)
                if isinstance(data, EnumChoice):
                    return data.choice
                return data

            def to_representation(self, obj):
                obj = super().to_representation(obj)
                if isinstance(obj, EnumChoice):
                    return obj.choice.name
                elif isinstance(obj, Enum):
                    return obj.name
                return obj

        class DRFReadOnlyEnumField(serializers.CharField):
            def to_representation(self, obj):
                return str(obj.name)

        serializers.ModelSerializer.serializer_choice_field = DRFEnumChoiceField
        serializers.ModelSerializer.serializer_field_mapping[
            EnumField
        ] = DRFReadOnlyEnumField

    except ImportError:
        pass
