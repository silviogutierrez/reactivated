"""``Pick`` and friends at their public home.

The implementation currently lives in ``reactivated.rpc.core`` for
historical reasons; extracting it is a mechanical follow-up. Import from
here (or from ``reactivated`` directly) — not from ``rpc``.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # The mypy plugin resolves every pick() class against the generated
    # pick_schema module, which mypy only analyzes if some top-level import
    # puts it in the module graph. This is that import; without it the only
    # edge is a function-level import inside a decorator closure in
    # rpc.core, which mypy follows only by accident of graph topology.
    import pick_schema as pick_schema

from .rpc.core import FieldSegment as FieldSegment
from .rpc.core import InlinePick as InlinePick
from .rpc.core import LazyStr as LazyStr
from .rpc.core import Pick as Pick
from .rpc.core import PickArgs as PickArgs
from .rpc.core import PickAsDict as PickAsDict
from .rpc.core import PickProxy as PickProxy
from .rpc.core import Primitive as Primitive
from .rpc.core import computed_property as computed_property
from .rpc.core import export as export
from .rpc.core import get_field_descriptor as get_field_descriptor
from .rpc.core import pick as pick

__all__ = [
    "FieldSegment",
    "InlinePick",
    "LazyStr",
    "Pick",
    "PickArgs",
    "PickAsDict",
    "PickProxy",
    "Primitive",
    "computed_property",
    "export",
    "get_field_descriptor",
    "pick",
]
