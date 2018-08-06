from typing import Any, Union, List, Optional

import io


class HttpResponse(object):
    def __init__(self, content: Union[str, io.StringIO], content_type: str = Optional[None]) -> None: ...


class HttpResponsePermanentRedirect(HttpResponse): ...

class HttpResponseRedirect(HttpResponse): ...

class Http404(Exception): ...
