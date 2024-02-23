from typing import TYPE_CHECKING, Any, List, Optional, Type, TypeVar, Union

if TYPE_CHECKING:
    T = TypeVar("T")

    class _GenericAlias:
        __origin__: Union[type, Any]
        __args__: List[Any]

    class _LiteralGenericAlias:
        __args__: List[Any]

    class _TypedDictMeta:
        pass

    Undefined = Optional[T]
else:
    from typing import _GenericAlias, _LiteralGenericAlias, _TypedDictMeta  # noqa: F401

    class BaseUndefinedHolder:
        _reactivated_undefined = True
        type: Any

        @classmethod
        def get_json_schema(cls: Type["BaseUndefinedHolder"], definitions: Any) -> Any:
            from .serialization import create_schema

            return create_schema(cls.type, definitions)

    class Undefined:
        wrapped: Any

        def __class_getitem__(cls: Type["Undefined"], item: Any) -> Any:
            class Undefined(BaseUndefinedHolder):
                type = item

            return Undefined
