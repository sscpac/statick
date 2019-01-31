"""Discovery plugin."""
import os
import sys

from yapsy.IPlugin import IPlugin


class DiscoveryPlugin(IPlugin):
    """Default implementation of discovery plugin."""

    plugin_context = None

    def get_name(self):
        """Get name of plugin."""
        pass

    def gather_args(self, args):
        """Gather arguments for plugin."""
        pass

    def scan(self, package, level):
        """Scan package to discover files for analysis."""
        pass

    def set_plugin_context(self, plugin_context):
        """Set the plugin context."""
        self.plugin_context = plugin_context

    @staticmethod
    def file_command_exists():
        """Return whether the 'file' command is available on $PATH"""
        if sys.platform == 'win32':
            command_name = 'file.exe'
        else:
            command_name = 'file'

        for path in os.environ["PATH"].split(os.pathsep):
            exe_path = os.path.join(path, command_name)
            if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                return True

        return False
