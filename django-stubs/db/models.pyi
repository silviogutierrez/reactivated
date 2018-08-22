from typing import Any, Optional

class Model:
    id: Optional[int]
    pk: Optional[int]

    def save(self, *args: Any, **kwargs: Any) -> None: ...

CharField: Any
BooleanField: Any
ForeignKey: Any
TextField: Any
SlugField: Any
IntegerField: Any
ManyToManyField: Any
DateTimeField: Any
EmailField: Any

CASCADE: Any
