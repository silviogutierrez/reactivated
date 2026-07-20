class ApiError(Exception):
    """Raise from an RPC handler to signal invalid input to the client.

    Explicit successor to the ``raise AssertionError(...)`` idiom, which is
    stripped under ``python -O``. Always produces a 400 response whose body is
    ``messages``, mirroring pydantic validation failures.

    Non-400 business outcomes (e.g. "already submitted", "feature disabled")
    are not errors: model them as discriminated success outputs — a 200 body
    carrying a status field the client switches on — not HTTP error codes.
    """

    def __init__(self, *messages: str) -> None:
        super().__init__(*messages)
        self.messages: list[str] = list(messages)
