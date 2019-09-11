from __future__ import annotations

from typing import Any


class Pick:
    def __class_getitem__(cls: Any, item: Any) -> Any:
        return cls
