"""Apply bandit tool and gather results."""

from __future__ import print_function
import csv
import subprocess
import shlex

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


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
        elif len(package["python_src"]) == 0:
            return []

        bandit_bin = "bandit"
        if self.plugin_context.args.bandit_bin is not None:
            bandit_bin = self.plugin_context.args.bandit_bin

        flags = ["--format=csv"]
        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = flags + list(lex)

        files = []
        if "python_src" in package:
            files += package["python_src"]

        try:
            output = subprocess.check_output([bandit_bin] + flags + files,
                                             stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("bandit failed! Returncode = {}".
                      format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find %s! (%s)" % (bandit_bin, ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output()
        return issues

    def parse_output(self):
        """Parse tool output and report issues."""
        issues = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        try:
            with open('bandit_results.csv', 'r') as csvfile:
                csvreader = csv.reader(csvfile, quoting=csv.QUOTE_MINIMAL)
                for line in csvreader:
                    if len(line) < 7:
                        continue
                    if line[0] == 'filename':
                        # Skip the column header line
                        continue
                    cert_reference = None
                    if line[1] in warnings_mapping.keys():
                        cert_reference = warnings_mapping[line[1]]
                    severity = 1
                    if line[4] == "MEDIUM":
                        severity = 3
                    elif line[4] == "HIGH":
                        severity = 5
                    issues.append(Issue(line[0], line[5],
                                        self.get_name(), line[1],
                                        severity, line[4], cert_reference))
        except IOError:
            # We couldn't find the results file for some reason
            pass

        return issues
