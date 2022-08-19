"""Timing interface."""

from typing import NamedTuple

Timing = NamedTuple(
    "Timing",
    [
        ("name", str),
        ("plugin_type", str),
        ("duration", str),
    ],
)
