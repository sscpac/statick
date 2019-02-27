"""Write issue reports to the console."""
from __future__ import print_function

from collections import OrderedDict

from six import iteritems

from statick_tool.reporting_plugin import ReportingPlugin


class PrintToConsoleReportingPlugin(ReportingPlugin):
    """Prints the Statick reports out to the terminal."""

    def get_name(self):
        """Return the name of the plugin."""
        return "print_to_console"

    def report(self, package, issues, level):
        """
        Go through the issues list and print them to the console.

        Args:
            package (:obj:`Package`): The Package object that was analyzed.
            issues (:obj:`dict` of :obj:`str` to :obj:`Issue`): The issues
                found by the Statick analysis, keyed by the tool that found
                them.
            level: (:obj:`str`): Name of the level used in the scan
        """
        total = 0
        for key, value in iteritems(issues):
            unique_issues = list(OrderedDict.fromkeys(value))
            print("Tool {}: {} unique issues".format(key, len(unique_issues)))
            for issue in unique_issues:
                if issue.cert_reference:
                    print("  {}:{}: {}:{}: {} ({}) [{}]".format(issue.filename,
                                                                issue.line_number,
                                                                issue.tool,
                                                                issue.issue_type,
                                                                issue.message,
                                                                issue.cert_reference,
                                                                issue.severity))
                else:
                    print("  {}:{}: {}:{}: {} [{}]".format(issue.filename,
                                                           issue.line_number,
                                                           issue.tool,
                                                           issue.issue_type,
                                                           issue.message,
                                                           issue.severity))

            total += len(unique_issues)
        print("{} total unique issues".format(total))
