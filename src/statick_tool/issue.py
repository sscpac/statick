"""Issue interface."""

from typing import NamedTuple, Optional

Issue = NamedTuple(
    "Issue",
    [
        ("filename", str),
        ("line_number", int),
        ("tool", str),
        ("issue_type", str),
        ("severity", int),
        ("message", str),
        ("cert_reference", Optional[str]),
    ],
)
