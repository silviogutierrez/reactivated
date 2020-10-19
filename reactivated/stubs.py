from typing import TYPE_CHECKING, Any, ClassVar, List, Mapping, Type, Union

if TYPE_CHECKING:
    from django import forms as django_forms

    class BaseForm(django_forms.BaseForm):
        base_fields: ClassVar[Mapping[str, django_forms.fields.Field]]

    class BaseFormSet(django_forms.formsets.BaseFormSet):
        form: ClassVar[Type[BaseForm]]

        def total_form_count(self) -> int:
            ...

        def initial_form_count(self) -> int:
            ...

        def non_form_errors(self) -> Any:
            ...

        # Our plugin adds this.
        # def is_valid(self) -> bool:
        #    pass

        can_order: bool
        can_delete: bool
        max_num: int
        min_num: int
        extra: int

    class BaseModelFormSet(BaseFormSet, django_forms.models.BaseModelFormSet):
        pass

    class _GenericAlias:
        __origin__: Union[type, Any]
        __args__: List[Any]

    class _TypedDictMeta:
        pass


else:
    from typing import _GenericAlias, _TypedDictMeta  # noqa: F401
    from django.forms.formsets import BaseFormSet  # noqa: F401
