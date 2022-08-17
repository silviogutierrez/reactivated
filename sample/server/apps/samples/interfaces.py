from typing import List, NamedTuple

from reactivated import Pick, interface

from . import models


MyPick = Pick[models.Opera, "id", "name"]


@interface
class OperaList(NamedTuple):
    operas: List[Pick[models.Opera, "name"]]
    operas: MyPick
