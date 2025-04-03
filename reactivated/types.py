from typing import Literal, NamedTuple, TypedDict, Union

from django import forms


class RPC(TypedDict):
    params: list[tuple[str, str]]
    url: str
    input: str | None
    output: str
    type: Literal["form", "form_set", "form_group"]


RPCRegistry = dict[str, RPC]


class OptgroupMember(NamedTuple):
    name: str
    value: str | int | bool | None
    label: str
    selected: bool


Optgroup = tuple[None, tuple[OptgroupMember], int]


Widget = Union[
    forms.HiddenInput,
    forms.TextInput,
    forms.NumberInput,
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


class URL(TypedDict):
    route: str
    args: dict[str, str]


URLSchema = dict[str, URL]


class Types(NamedTuple):
    Widget: Widget
    Optgroup: Optgroup
    URLSchema: URLSchema
    RPCRegistry: RPCRegistry
