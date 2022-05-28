from typing import Dict, List, Literal, NamedTuple, Optional, Tuple, TypedDict, Union

from django import forms


class RPC(TypedDict):
    params: List[Tuple[str, str]]
    url: str
    input: Optional[str]
    output: str
    type: Literal["form", "form_set", "form_group"]


RPCRegistry = Dict[str, RPC]


class OptgroupMember(NamedTuple):
    name: str
    value: Union[str, int, bool, None]
    label: str
    selected: bool


Optgroup = Tuple[None, Tuple[OptgroupMember], int]


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
    args: Dict[str, str]


URLSchema = Dict[str, URL]


class Types(NamedTuple):
    Widget: Widget
    Optgroup: Optgroup
    URLSchema: URLSchema
    RPCRegistry: RPCRegistry
