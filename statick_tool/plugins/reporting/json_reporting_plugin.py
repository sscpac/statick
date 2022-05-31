"""Prints the Statick reports out to the terminal or file in JSON format."""
import json
import logging
import os
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class JsonReportingPlugin(ReportingPlugin):
    """Prints the Statick reports out to the terminal or file in JSON format."""

    def get_name(self) -> str:
        """Return the plugin name."""
        return "json"

    def report(
        self, package: Package, issues: Dict[str, List[Issue]], level: str
    ) -> Tuple[Optional[None], bool]:
        """Go through the issues list and print them in JSON format.

        Args:
            package (:obj:`Package`): The Package object that was analyzed.
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): The issues
                found by the Statick analysis, keyed by the tool that found
                them.
            level: (:obj:`str`): Name of the level used in the scan.
        """
        if not self.plugin_context or not self.plugin_context.config:
            return None, False

        file_output = False
        terminal_output = False
        file_output_str = self.plugin_context.config.get_reporting_config(
            self.get_name(), level, "files"
        )
        if file_output_str and file_output_str.lower() == "true":
            file_output = True
        terminal_output_str = self.plugin_context.config.get_reporting_config(
            self.get_name(), level, "terminal"
        )
        if terminal_output_str and terminal_output_str.lower() == "true":
            terminal_output = True

        all_issues = []
        for _, value in issues.items():
            for issue in value:
                issue_dict = OrderedDict()
                issue_dict["fileName"] = issue.filename
                issue_dict["lineNumber"] = issue.line_number
                issue_dict["tool"] = issue.tool
                issue_dict["type"] = issue.issue_type
                issue_dict["severity"] = issue.severity
                issue_dict["message"] = issue.message
                issue_dict["certReference"] = ""
                if issue.cert_reference:
                    issue_dict["certReference"] = issue.cert_reference
                all_issues.append(issue_dict)
        report_json = {"issues": all_issues}
        line = json.dumps(report_json)

        if file_output:
            if not self.write_output(package, level, line):
                return None, False

        if terminal_output:
            print(line)

        return None, True

    def write_output(self, package: Package, level: str, line: str) -> bool:
        """Write JSON output to a file."""
        if not self.plugin_context:
            return False

        output_dir = os.path.join(
            self.plugin_context.args.output_directory, package.name + "-" + level
        )
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            logging.error("Unable to create output directory at %s!", output_dir)
            return False
        output_file = os.path.join(output_dir, package.name + "-" + level + ".json")
        next_output_file = os.path.join(
            output_dir, package.name + "-" + level + ".statick.json"
        )
        logging.warning(
            "Output filename will change in statick v0.9.0 from %s to %s",
            output_file,
            next_output_file,
        )
        logging.info("Writing output to %s", output_file)
        with open(output_file, "w", encoding="utf8") as out:
            out.write(line)

        return True
