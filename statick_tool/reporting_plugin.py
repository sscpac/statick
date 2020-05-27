"""Result reporting plugin."""
import argparse
from typing import Dict, List, Optional, Tuple, Union

from yapsy.IPlugin import IPlugin

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class ReportingPlugin(IPlugin):  # type: ignore
    """Default implementation of reporting plugin."""

    plugin_context = None

    def get_name(self) -> Optional[str]:
        """Get name of reporting plugin."""

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""

    def report(
        self, package: Package, issues: Dict[str, List[Issue]], level: str
    ) -> Tuple[Optional[None], bool]:
        """Run the report generator."""

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Setter for plugin_context."""
        self.plugin_context = plugin_context
