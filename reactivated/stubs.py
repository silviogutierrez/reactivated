from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:

    class _GenericAlias:
        __origin__: type
        __args__: List[Any]


else:
    from typing import _GenericAlias  # noqa: F401
