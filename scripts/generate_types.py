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

import pprint

pprint.pprint(simplejson.loads(schema))

encoded_schema = schema.encode()

process = subprocess.Popen(
    ["npm", "exec", "json2ts"],
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
)
out, error = process.communicate(encoded_schema)

with open("packages/reactivated/src/generated.tsx", "w+b") as output:
    output.write(out)
