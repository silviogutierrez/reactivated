from __future__ import annotations

from typing import Any, TYPE_CHECKING


class BasePickHolder:
    pass


class Pick:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        meta_model, *meta_fields = item

        class PickHolder(BasePickHolder):
            model = meta_model
            fields = meta_fields

        return PickHolder
