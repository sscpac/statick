"""Write issue reports to screen and file."""

from __future__ import print_function

from collections import OrderedDict


def write_report_file(issues, filename):
    """Format issues into a new file format."""
    with open(filename, "w") as out:
        for dummy, value in list(issues.items()):
            for issue in value:
                if issue.cert_reference:
                    line = "[%s][%s][%s:%s][%s (%s)][%s]\n" % (issue.filename,
                                                               issue.line_number,
                                                               issue.tool,
                                                               issue.issue_type,
                                                               issue.message,
                                                               issue.cert_reference,
                                                               issue.severity)
                else:
                    line = "[%s][%s][%s:%s][%s][%s]\n" % (issue.filename,
                                                          issue.line_number,
                                                          issue.tool,
                                                          issue.issue_type,
                                                          issue.message,
                                                          issue.severity)
                out.write(line)


def generate_report(issues, output_filename):
    """Print report to screen."""
    total = 0
    print("---Report---")
    for key, value in list(issues.items()):
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
    print("---Report---")
    print("{} total unique issues".format(total))
    print("---Report---")

    write_report_file(issues, output_filename)
    print("Report written to {}".format(output_filename))
