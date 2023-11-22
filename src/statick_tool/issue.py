"""Issue interface."""

from typing import NamedTuple, Optional

# It would be nice to change line_number and severity types to int.
# We need to coordinate that change with other packages containing tool and
# reporting plugins to make sure nothing breaks.
Issue = NamedTuple(
    "Issue",
    [
        ("filename", str),
        ("line_number", str),
        ("tool", str),
        ("issue_type", str),
        ("severity", str),
        ("message", str),
        ("cert_reference", Optional[str]),
    ],
)
