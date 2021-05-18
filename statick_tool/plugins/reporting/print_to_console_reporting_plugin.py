"""Write issue reports to the console."""
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class PrintToConsoleReportingPlugin(ReportingPlugin):
    """Prints the Statick reports out to the terminal."""

    def get_name(self) -> str:
        """Return the name of the plugin."""
        return "print_to_console"

    def report(
        self, package: Package, issues: Dict[str, List[Issue]], level: str
    ) -> Tuple[Optional[None], bool]:
        """Go through the issues list and print them to the console.

        Args:
            package (:obj:`Package`): The Package object that was analyzed.
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): The issues
                found by the Statick analysis, keyed by the tool that found
                them.
            level: (:obj:`str`): Name of the level used in the scan
        """
        total: int = 0
        for key, value in issues.items():
            unique_issues = list(OrderedDict.fromkeys(value))
            num_issues = len(unique_issues)
            print(f"Tool {key}: {num_issues} unique issues")
            for issue in unique_issues:
                if issue.cert_reference:
                    print(
                        f"  {issue.filename}:{issue.line_number}: "
                        f"{issue.tool}:{issue.issue_type}: {issue.message} "
                        f"({issue.cert_reference}) [{issue.severity}]"
                    )
                else:
                    print(
                        f"  {issue.filename}:{issue.line_number}: "
                        f"{issue.tool}:{issue.issue_type}: {issue.message} "
                        f"[{issue.severity}]"
                    )

            total += len(unique_issues)
        print(f"{total} total unique issues")

        return None, True
