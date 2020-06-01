from typing import TYPE_CHECKING, Any, ClassVar, List, Type, Union

if TYPE_CHECKING:
    from django import forms as django_forms

    class BaseFormSet(django_forms.formsets.BaseFormSet):
        form: ClassVar[Type[django_forms.BaseForm]]

        def total_form_count(self) -> int:
            ...

        def initial_form_count(self) -> int:
            ...

        def non_form_errors(self) -> Any:
            ...

        can_order: bool
        can_delete: bool
        max_num: int
        min_num: int

    class _GenericAlias:
        __origin__: Union[type, Any]
        __args__: List[Any]

    class _TypedDictMeta:
        pass


else:
    from typing import _GenericAlias, _TypedDictMeta  # noqa: F401
    from django.forms.formsets import BaseFormSet  # noqa: F401
