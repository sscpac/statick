"""Prints the Statick reports out to the terminal in JSON format."""
import json
from typing import Dict, List, Optional, Tuple

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class PrintJsonReportingPlugin(ReportingPlugin):
    """Prints the Statick reports out to the terminal in JSON format."""

    def get_name(self) -> str:
        """Return the plugin name."""
        return "print_json"

    def report(
        self, package: Package, issues: Dict[str, List[Issue]], level: str
    ) -> Tuple[Optional[None], bool]:
        """Go through the issues list and print them to the console in JSON format.

        Args:
            package (:obj:`Package`): The Package object that was analyzed.
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): The issues
                found by the Statick analysis, keyed by the tool that found
                them.
            level: (:obj:`str`): Name of the level used in the scan.
        """
        all_issues = []
        for _, value in issues.items():
            for issue in value:
                issue_dict = {
                    "fileName": issue.filename,
                    "lineNumber": issue.line_number,
                    "tool": issue.tool,
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                if issue.cert_reference:
                    issue_dict["certReference"] = issue.cert_reference
                else:
                    issue_dict["certReference"] = ""
                all_issues.append(issue_dict)
        report_json = {"issues": all_issues}
        line = json.dumps(report_json)
        print(line)

        return None, True
