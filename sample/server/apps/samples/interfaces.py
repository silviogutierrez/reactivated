from typing import List, NamedTuple

from reactivated import Pick, interface

from . import models


@interface
class OperaList(NamedTuple):
    operas: List[Pick[models.Opera, "name"]]
