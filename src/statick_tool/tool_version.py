"""Tool version interface."""

from typing import NamedTuple

ToolVersion = NamedTuple(
    "ToolVersion",
    [
        ("tool", str),
        ("version", str),
    ],
)
