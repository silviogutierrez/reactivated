from typing import NamedTuple


from reactivated import template


@template
class DjangoDefault(NamedTuple):
    version: str


adapters = {
    "default_urlconf.html": DjangoDefault,
}
