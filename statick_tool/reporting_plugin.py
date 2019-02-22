"""Result reporting plugin."""
from yapsy.IPlugin import IPlugin


class ReportingPlugin(IPlugin):
    """Default implementation of reporting plugin."""

    plugin_context = None

    def get_name(self):
        """Get name of reporting plugin."""

    def gather_args(self, args):
        """Gather arguments."""

    def report(self, package, issues, level):
        """Run the report generator."""

    def set_plugin_context(self, plugin_context):
        """Setter for plugin_context."""
        self.plugin_context = plugin_context
