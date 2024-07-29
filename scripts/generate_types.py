import subprocess

import django
import django_stubs_ext
import simplejson
from django.conf import settings

# Django needs to be configured because of reactivated's monkey patching of
# runserver_plus.
settings.configure()
django.setup()


django_stubs_ext.monkeypatch()


from reactivated.serialization import create_schema  # noqa: E402
from reactivated.types import Types  # noqa: E402

types_schema = create_schema(Types, {})

schema = simplejson.dumps(
    {
        "$defs": types_schema.definitions,
        **types_schema.dereference(),
        "title": "Types",
    }
)

encoded_schema = schema.encode()

process = subprocess.Popen(
    ["npm", "exec", "json2ts"],
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
)
out, error = process.communicate(encoded_schema)

with open("packages/reactivated/src/generated.tsx", "w+b") as output:
    output.write(out)
