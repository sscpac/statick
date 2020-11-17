"""Discovery plugin."""
import os
import sys
from typing import Any, List, Optional, Union

from yapsy.IPlugin import IPlugin

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class DiscoveryPlugin(IPlugin):  # type: ignore
    """Default implementation of discovery plugin."""

    plugin_context = None

    def get_name(self) -> Optional[str]:
        """Get name of plugin."""

    @classmethod
    def get_discovery_dependencies(cls) -> List[str]:
        """Get a list of discovery plugins that must run before this one."""
        return []

    def gather_args(self, args: Any) -> None:
        """Gather arguments for plugin."""

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """
        Scan package to discover files for analysis.

        If exceptions is passed, then the plugin should (if practical)
        use it to filter which files the plugin detects.
        """

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Set the plugin context."""
        self.plugin_context = plugin_context

    @staticmethod
    def file_command_exists() -> bool:
        """Return whether the 'file' command is available on $PATH."""
        if sys.platform == "win32":
            command_name = "file.exe"
        else:
            command_name = "file"

        for path in os.environ["PATH"].split(os.pathsep):
            exe_path = os.path.join(path, command_name)
            if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                return True

        return False
