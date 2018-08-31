"""
Manages plugin and file lookup chaining.

Handles chainging user directories and the default statick resource directory.
"""

from __future__ import print_function
import os


class Resources(object):
    """
    Manages plugin and file lookup chaining.

    Handles chainging user directories and the default statick resource
    directory.
    """

    def __init__(self, paths):
        """Initialize resource handling."""
        self.paths = []

        for path in paths:
            if os.path.exists(path) and os.path.isdir(path):
                self.paths.append(os.path.abspath(path))
            else:
                print("Could not find path {}".format(path))

        default_path = os.path.dirname(__file__)
        self.paths.append(default_path)

    def get_plugin_paths(self):
        """Get paths where plugins are located."""
        plugin_paths = []
        for path in self.paths:
            full_path = os.path.join(path, "plugins")
            if os.path.exists(full_path) and os.path.isdir(full_path):
                plugin_paths.append(full_path)
        return plugin_paths

    def get_file(self, filename):
        """Get full path to file for default and user-defined resource paths."""
        for path in self.paths:
            full_filename = os.path.join(path, "rsc", filename)
            if os.path.exists(full_filename) and os.path.isfile(full_filename):
                return full_filename
        return None
