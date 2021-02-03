"""Do nothing to have a default reporting plugin with no side effects."""
from typing import Dict, List, Optional, Tuple

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class DoNothingReportingPlugin(ReportingPlugin):
    """Do nothing."""

    def get_name(self) -> str:
        """Return the name of the plugin."""
        return "do_nothing"

    def report(
        self, package: Package, issues: Dict[str, List[Issue]], level: str
    ) -> Tuple[Optional[None], bool]:
        """Do nothing."""
        return None, True
