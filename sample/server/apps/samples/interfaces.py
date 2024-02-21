from typing import List, NamedTuple

from reactivated import Pick, interface

from . import models


Opera = Pick(models.Opera, fields=["name"])


@interface
class OperaList(NamedTuple):
    operas: List[Opera]
