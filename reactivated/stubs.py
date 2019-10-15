from typing import TYPE_CHECKING, Any, List, Union, Optional, NamedTuple, Dict

if TYPE_CHECKING:

    class _GenericAlias:
        __origin__: Union[type, Any]
        __args__: List[Any]


else:
    from typing import _GenericAlias  # noqa: F401


class FieldType(NamedTuple):
    name: str
    label: str
    help_text: str
    # widget: WidgetType


FormError = Optional[List[str]]

FormErrors = Dict[str, FormError]


class FormType(NamedTuple):
    errors: Optional[FormErrors]
    fields: Dict[str, FieldType]
    iterator: List[str]
    prefix: str
    is_read_only: bool = False
