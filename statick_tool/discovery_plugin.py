"""Discovery plugin."""
import os
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
        return os.path.isfile('file') and os.access(fpath, os.X_OK)
