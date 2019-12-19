"""Apply bandit tool and gather results."""

from __future__ import print_function

import csv
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class BanditToolPlugin(ToolPlugin):
    """Apply bandit tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "bandit"

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("--bandit-bin", dest="bandit_bin", type=str,
                          help="bandit binary path")

    def scan(self, package, level):
        """Run tool and gather output."""
        if "python_src" not in package:
            return []
        if not package["python_src"]:
            return []

        bandit_bin = "bandit"
        if self.plugin_context.args.bandit_bin is not None:
            bandit_bin = self.plugin_context.args.bandit_bin

        flags = ["--format=csv"]
        flags += self.get_user_flags(level)

        files = []
        if "python_src" in package:
            files += package["python_src"]

        try:
            output = subprocess.check_output([bandit_bin] + flags + files,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("bandit failed! Returncode = {}".
                      format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find {}! ({})".format(bandit_bin, ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output(output.splitlines())
        return issues

    def parse_output(self, output):
        """Parse tool output and report issues."""
        issues = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()

        # Copy output for modification
        output_minus_log = list(output)

        # Bandit prints a bunch of log messages out and you can't suppress
        # them, so iterate over the list until we find the CSV header
        for line in output:  # Intentionally output, not output_minus_log
            if line.startswith('filename'):
                # Found the CSV header, stop removing things
                break
            output_minus_log.remove(line)

        csvreader = csv.DictReader(output_minus_log)
        for line in csvreader:
            cert_reference = None
            if line['test_id'] in warnings_mapping:
                cert_reference = warnings_mapping[line['test_id']]
            severity = '1'
            if line['issue_confidence'] == "MEDIUM":
                severity = '3'
            elif line['issue_confidence'] == "HIGH":
                severity = '5'
            issues.append(Issue(line['filename'], line['line_number'],
                                self.get_name(), line['test_id'],
                                severity, line['issue_text'], cert_reference))

        return issues
