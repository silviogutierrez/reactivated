from reactivated import Pick, pick

from . import models

OperaName = pick(models.Opera, fields=["name"])


class OperaList(Pick):
    operas: list[OperaName.output]
