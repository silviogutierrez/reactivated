import subprocess

import simplejson

from reactivated.serialization import create_schema
from reactivated.types import Types

types_schema = create_schema(Types, {})

schema = simplejson.dumps(
    {
        "title": "Types",
        "definitions": types_schema.definitions,
        **types_schema.dereference(),
    }
)

encoded_schema = schema.encode()

process = subprocess.Popen(
    ["./packages/reactivated/node_modules/.bin/json2ts"],
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
)
out, error = process.communicate(encoded_schema)

with open("packages/reactivated/generated.tsx", "w+b") as output:
    output.write(out)
