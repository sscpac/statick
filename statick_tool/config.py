"""
Manages which plugins are run for each statick scan level.

Sets what flags are used for each plugin at those levels.
"""
import os
from collections import OrderedDict
from typing import Any, List, Optional

import yaml


class Config:
    """
    Manages which plugins are run for each statick scan level.

    Sets what flags are used for each plugin at those levels.
    """

    def __init__(self, filename: Optional[str]) -> None:
        """Initialize configuration."""
        if filename is None or not os.path.exists(filename):
            self.config = []  # type: Any
            return
        with open(filename) as fname:
            self.config = yaml.safe_load(fname)

    def has_level(self, level: Optional[str]) -> bool:
        """Check if given level exists in config."""
        return "levels" in self.config and level in self.config["levels"]

    def get_enabled_plugins(self, level: str, plugin_type: str) -> List:
        """Get what plugins are enabled for a certain level."""
        level_config = self.config["levels"][level]
        plugins = []  # type: List
        if plugin_type in level_config:
            plugins += list(level_config[plugin_type])
        if "inherits_from" in level_config:
            inherited_level = level_config["inherits_from"]
            plugins += self.get_enabled_plugins(inherited_level, plugin_type)
        plugins = list(OrderedDict.fromkeys(plugins))
        return plugins

    def get_enabled_tool_plugins(self, level: str) -> List:
        """Get what tool plugins are enabled for a certain level."""
        return self.get_enabled_plugins(level, "tool")

    def get_enabled_discovery_plugins(self, level: str) -> List:
        """Get what discovery plugins are enabled for a certain level."""
        return self.get_enabled_plugins(level, "discovery")

    def get_enabled_reporting_plugins(self, level: str) -> List:
        """Get what reporting plugins are enabled for a certain level."""
        return self.get_enabled_plugins(level, "reporting")

    def get_plugin_config(  # pylint: disable=too-many-arguments
        self, plugin_type: str, plugin: str, level: str, key: str, default=None,
    ) -> str:
        """Get flags to use for a plugin at a certain level."""
        if level not in self.config["levels"].keys():
            return default
        level_config = self.config["levels"][level]
        if plugin_type in level_config:
            type_config = level_config[plugin_type]
            if plugin in type_config:
                plugin_config = type_config[plugin]
                if key in plugin_config:
                    return plugin_config[key]
        if "inherits_from" in level_config:
            inherited_level = level_config["inherits_from"]
            return self.get_plugin_config(
                plugin_type, plugin, inherited_level, key, default
            )
        return default

    def get_tool_config(self, plugin: str, level: str, key: str, default=None) -> str:
        """Get tool flags to use for a plugin at a certain level."""
        return self.get_plugin_config("tool", plugin, level, key, default)

    def get_discovery_config(
        self, plugin: str, level: str, key: str, default=None
    ) -> Optional[str]:
        """Get discovery flags to use for a plugin at a certain level."""
        return self.get_plugin_config("discovery", plugin, level, key, default)

    def get_reporting_config(
        self, plugin: str, level: str, key: str, default=None
    ) -> Optional[str]:
        """Get reporting flags to use for a plugin at a certain level."""
        return self.get_plugin_config("reporting", plugin, level, key, default)
