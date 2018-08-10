from typing import Any, Dict, List, Optional, Iterator

class BaseForm:
    cleaned_data: Dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def is_valid(self) -> bool: ...

    errors: Dict[str, Optional[List[str]]]

    def __iter__(self) -> Iterator[Any]: ...

class Form(BaseForm): ...

class ModelForm(Form):
    def save(self, commit=False) -> Any: ...
