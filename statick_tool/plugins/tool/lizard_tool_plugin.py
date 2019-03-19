"""Apply lizard tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class LizardToolPlugin(ToolPlugin):
    """Apply Lizard tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "lizard"

    def scan(self, package, level):
        """Run tool and gather output."""
        output = None

        src_dir = '.'
        if "src_dir" in package:
            src_dir = package["src_dir"]

        try:
            output = subprocess.check_output(["lizard", "-w", src_dir],
                                             universal_newlines=True)
        except subprocess.CalledProcessError as ex:
            if ex.returncode == 1:
                output = ex.output
            else:
                print("Problem {}".format(ex.returncode))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find lizard executable! ({})".format(ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output(output)
        return issues

    def parse_output(self, output):
        """Parse tool output and report issues."""
        lizard_re = r"(.+):(\d+):\s(.+):\s(.+)"
        parse = re.compile(lizard_re)
        matches = []
        for line in output.splitlines():
            match = parse.match(line)
            if match:
                matches.append(match.groups())

        issues = []
        for match in matches:
            issue = Issue(match[0], match[1], self.get_name(), match[2], "5",
                          match[3], None)
            if issue not in issues:
                issues.append(issue)

        return issues
