"""Do nothing, this is primarily useful for testing purposes."""

from importlib.metadata import version
from typing import Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DoNothingToolPlugin(ToolPlugin):
    """Do nothing, this is primarily useful for testing purposes."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "do_nothing"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan."""
        return []

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output."""
        return []

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""
        return []

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed."""
        return version("statick")
