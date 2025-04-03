from typing import NamedTuple

from reactivated import Pick, interface

from . import models


@interface
class OperaList(NamedTuple):
    operas: list[Pick[models.Opera, "name"]]
