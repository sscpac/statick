"""Do nothing, this is primarily useful for testing purposes."""
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DoNothingToolPlugin(ToolPlugin):
    """Do nothing, this is primarily useful for testing purposes."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "do_nothing"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return []

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        return []

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        return []
