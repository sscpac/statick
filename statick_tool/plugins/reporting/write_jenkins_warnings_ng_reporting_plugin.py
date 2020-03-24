"""Write Statick results to Jenkins Warnings-NG plugin json-log compatible output."""
import json
import os
from typing import Dict, Optional, Tuple

from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class WriteJenkinsWarningsNGReportingPlugin(ReportingPlugin):
    """Writes Statick results to Jenkins Warnings-NG plugin json-log compatible output."""

    def get_name(self) -> str:
        """Return the plugin name."""
        return "write_jenkins_warnings_ng"

    def report(
        self, package: Package, issues: Dict, level: str
    ) -> Tuple[Optional[None], bool]:
        """
        Write the results to Jenkins Warnings-NG plugin compatible file.

        Args:
            package (:obj:`Package`): The Package object that was analyzed.
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): The issues
                found by the Statick analysis, keyed by the tool that found
                them.
            level: (:obj:`str`): Name of the level used in the scan.
        """
        if self.plugin_context is None:
            return None, False

        # Do not write report to file if no output directory is given.
        if not self.plugin_context.args.output_directory:
            return None, True

        # We _should_ be in output_dir already, but let's be safe about it.
        output_dir = os.path.join(
            self.plugin_context.args.output_directory, package.name + "-" + level
        )

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            print("Unable to create output directory at {}!".format(output_dir))
            return None, False

        output_file = os.path.join(
            output_dir, package.name + "-" + level + ".json.statick"
        )
        print("Writing output to {}".format(output_file))
        with open(output_file, "w") as out:
            for _, value in issues.items():
                for issue in value:
                    severity = "LOW"
                    try:
                        if int(issue.severity) > 0:
                            severity = "NORMAL"
                        if int(issue.severity) > 2:
                            severity = "HIGH"
                        if int(issue.severity) > 4:
                            severity = "ERROR"
                    except ValueError as ex:
                        print(
                            "Invalid severity integer ({}), using default 'LOW' severity. "
                            "Error = {}".format(issue.severity, ex)
                        )
                    issue_dict = {
                        "fileName": issue.filename,
                        "severity": severity,
                        "lineStart": issue.line_number,
                        "message": issue.message,
                        "category": issue.tool,
                        "type": issue.issue_type,
                    }
                    line = json.dumps(issue_dict, sort_keys=True) + "\n"
                    out.write(line)

        return None, True
