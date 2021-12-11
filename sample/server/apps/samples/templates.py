from typing import NamedTuple

from reactivated import Pick, template

from . import models


@template
class HelloWorld(NamedTuple):
    opera: Pick[models.Opera, "name", "composer.name", "style"]
