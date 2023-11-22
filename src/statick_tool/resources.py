"""Manages plugin and file lookup chaining.

Handles chaining user directories and the default statick resource directory.
"""
import logging
import os
from typing import List, Optional


class Resources:
    """Manages plugin and file lookup chaining.

    Handles chaining user directories and the default statick resource directory.
    """

    def __init__(self, paths: List[str]) -> None:
        """Initialize resource handling."""
        self.paths: List[str] = []

        for path in paths:
            if os.path.exists(path) and os.path.isdir(path):
                self.paths.append(os.path.abspath(path))
                logging.debug("Adding %s to resources path", path)
            elif os.path.exists(path) and not os.path.isdir(path):
                logging.error("%s is not a directory and not used as a path", path)
            else:
                logging.error("Could not find path %s", path)

        default_path = os.path.dirname(__file__)
        self.paths.append(default_path)

    def get_plugin_paths(self) -> List[str]:
        """Get paths where plugins are located."""
        plugin_paths = []
        for path in self.paths:
            full_path = os.path.join(path, "plugins")
            if os.path.exists(full_path) and os.path.isdir(full_path):
                plugin_paths.append(full_path)
        return plugin_paths

    def get_file(self, filename: str) -> Optional[str]:
        """Get full path to file for default and user-defined resource paths."""
        for path in self.paths:
            full_filename = os.path.join(path, "rsc", filename)
            if os.path.exists(full_filename) and os.path.isfile(full_filename):
                return full_filename
        return None
