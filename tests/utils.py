from __future__ import annotations

import enum
from typing import Literal

from reactivated.pick import Pick
from reactivated.utils import discriminate


def test_discriminate() -> None:
    """discriminate() builds a registry from a Literal-discriminated union."""

    class V1(Pick):
        version: Literal["v1"]

    class V2(Pick):
        version: Literal["v2"]

    assert discriminate(V1 | V2, "version") == {"v1": V1, "v2": V2}
    # A bare class (union of one) works before a second member exists.
    assert discriminate(V1, "version") == {"v1": V1}


def test_discriminate_by_enum_member() -> None:
    class Kind(enum.Enum):
        SEND_EMAIL = "SEND_EMAIL"

    class SendEmail(Pick):
        action: Literal[Kind.SEND_EMAIL]

    assert discriminate(SendEmail, "action") == {Kind.SEND_EMAIL: SendEmail}
