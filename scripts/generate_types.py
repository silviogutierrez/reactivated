import subprocess
from typing import NamedTuple, Union

import simplejson
from django import forms

from reactivated.serialization import create_schema, Optgroup

Widget = Union[
    forms.HiddenInput,
    forms.TextInput,
    forms.URLInput,
    forms.TimeInput,
    forms.DateInput,
    forms.CheckboxInput,
    forms.PasswordInput,
    forms.EmailInput,
    forms.Textarea,
    forms.Select,
    forms.SelectMultiple,
    forms.ClearableFileInput,
    forms.SelectDateWidget,
    forms.SplitDateTimeWidget,
]


class Types(NamedTuple):
    Widget: Widget
    Optgroup: Optgroup


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
