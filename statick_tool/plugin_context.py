"""Plugin context interface."""

from collections import namedtuple

PluginContext = namedtuple("PluginContext",
                           "args resources config")
