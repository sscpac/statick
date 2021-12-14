"""Manages which plugins are run for each statick scan level.

Sets what flags are used for each plugin at those levels.
"""
import os
from collections import OrderedDict
from typing import Any, List, Optional, Union

import yaml


class Config:
    """Manages which plugins are run for each statick scan level.

    Sets what flags are used for each plugin at those levels.
    """

    def __init__(self, base_file: Optional[str], user_file: Optional[str] = "") -> None:
        """Initialize configuration."""
        if base_file is None or not os.path.exists(base_file):
            self.config: Any = []
            return

        self.config = self.get_config_from_file(base_file)

        if user_file and os.path.exists(user_file):
            self.get_user_levels(user_file)

    def get_user_levels(self, user_file: str) -> None:
        """Get configuration levels from user file.

        Any levels in user file will be included in available levels. User levels can
        inherit from the base levels. If user levels and base levels have the same name
        the user level will override the base level.
        """
        user_config = self.get_config_from_file(user_file)
        if user_file:
            if "levels" in user_config:
                for level in user_config["levels"]:
                    level_config = user_config["levels"][level]
                    if (
                        level_config is not None
                        and "inherits_from" in level_config
                        and level_config["inherits_from"] == level
                    ):
                        level_config["inherits_from"] = ""
                    self.config["levels"][level] = user_config["levels"][level]

    @staticmethod
    def get_config_from_file(filename: str) -> Any:
        """Get level configuration from a file."""
        if filename:
            with open(filename, encoding="utf8") as fid:
                try:
                    return yaml.safe_load(fid)
                except (yaml.YAMLError, yaml.scanner.ScannerError) as ex:
                    raise ValueError(
                        f"{filename} is not a valid YAML file: {ex}"
                    ) from ex

        return None

    def has_level(self, level: Optional[str]) -> bool:
        """Check if given level exists in config."""
        return "levels" in self.config and level in self.config["levels"]

    def get_enabled_plugins(self, level: str, plugin_type: str) -> List[str]:
        """Get what plugins are enabled for a certain level."""
        plugins: List[str] = []
        print(f"level: {level}")
        print(f"plugin_type: {plugin_type}")
        print(f"config: {self.config['levels'][level]}")
        for level_type in self.config["levels"][level]:
            print(f"level_type: {level_type}")
            print(f"level[{level_type}]: {self.config['levels'][level][level_type]}")
            if plugin_type in level_type and self.config["levels"][level][plugin_type] is not None:
                print(f"Found desired plugin type {plugin_type}")
                plugins += list(self.config["levels"][level][plugin_type])
            if "inherits_from" in self.config["levels"][level]:
                for inherited_level in self.config["levels"][level]["inherits_from"]:
                    print(f"inherited_level: {inherited_level}")
                    enabled_plugins = self.get_enabled_plugins(inherited_level, plugin_type)
                    for plugin in enabled_plugins:
                        if plugin not in plugins:
                            plugins.append(plugin)
                    print(f"plugins for {inherited_level}: {plugins}")
                # plugins.append(list(OrderedDict.fromkeys(plugins)))
        print(f"**** {plugin_type} plugins: {plugins} ****")
        return plugins

    def get_enabled_tool_plugins(self, level: str) -> List[str]:
        """Get what tool plugins are enabled for a certain level."""
        print("Enabled tool plugins:")
        return self.get_enabled_plugins(level, "tool")

    def get_enabled_discovery_plugins(self, level: str) -> List[str]:
        """Get what discovery plugins are enabled for a certain level."""
        print("Enabled discovery plugins:")
        return self.get_enabled_plugins(level, "discovery")

    def get_enabled_reporting_plugins(self, level: str) -> List[str]:
        """Get what reporting plugins are enabled for a certain level."""
        print("Enabled reporting plugins:")
        return self.get_enabled_plugins(level, "reporting")

    def get_plugin_config(  # pylint: disable=too-many-arguments
        self,
        plugin_type: str,
        plugin: str,
        level: str,
        key: str,
        default: Optional[str] = None,
    ) -> Optional[Union[str, Any]]:
        """Get flags to use for a plugin at a certain level."""
        print(f"level: {level}")
        # print(f"config['levels']: {self.config['levels']}")
        if level not in self.config["levels"]:
            return default
        level_config = self.config["levels"][level]
        if plugin_type in level_config:
            type_config = level_config[plugin_type]
            if plugin in type_config:
                plugin_config = type_config[plugin]
                if plugin_config is not None and key in plugin_config:
                    return plugin_config[key]
        if "inherits_from" in level_config:
            inherited_level = level_config["inherits_from"]
            configs = ""
            for inherited_level in self.config["levels"][level]["inherits_from"]:
                config = self.get_plugin_config(
                    plugin_type, plugin, inherited_level, key, default
                )
                if config is not None:
                    configs += config
            print(f"plugin config: {configs}")
            return configs
        return default

    def get_tool_config(
        self, plugin: str, level: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get tool flags to use for a plugin at a certain level."""
        print("Get tool config.")
        return self.get_plugin_config("tool", plugin, level, key, default)

    def get_discovery_config(
        self, plugin: str, level: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get discovery flags to use for a plugin at a certain level."""
        print("Get discovery config.")
        return self.get_plugin_config("discovery", plugin, level, key, default)

    def get_reporting_config(
        self, plugin: str, level: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get reporting flags to use for a plugin at a certain level."""
        print("Get reporting config.")
        return self.get_plugin_config("reporting", plugin, level, key, default)
