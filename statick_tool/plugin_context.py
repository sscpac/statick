"""Plugin context interface."""

import argparse
from typing import NamedTuple

from statick_tool.config import Config
from statick_tool.resources import Resources

PluginContext = NamedTuple(
    "PluginContext",
    [("args", argparse.Namespace), ("resources", Resources), ("config", Config)],
)
