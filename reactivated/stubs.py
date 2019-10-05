from typing import TYPE_CHECKING, Any, List, Union

if TYPE_CHECKING:

    class _GenericAlias:
        __origin__: Union[type, Any]
        __args__: List[Any]


else:
    from typing import _GenericAlias  # noqa: F401
