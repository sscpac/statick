"""Timing interface."""

from typing import NamedTuple

Timing = NamedTuple(
    "Timing",
    [
        ("package", str),
        ("name", str),
        ("plugin_type", str),
        ("duration", str),
    ],
)
