"""Apply xmllint tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class XmllintToolPlugin(ToolPlugin):
    """Apply xmllint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "xmllint"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = []
        flags += self.get_user_flags(level)

        total_output = []

        for xml_file in package["xml"]:
            try:
                subproc_args = ["xmllint", xml_file] + flags
                output = subprocess.check_output(subproc_args,
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)
            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:
                    output = ex.output
                else:
                    print("Problem {}".format(ex.returncode))
                    print("{}".format(ex.output))
                    return None

            except OSError as ex:
                print("Couldn't find xmllint executable! ({})".format(ex))
                return None

            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))

            total_output.append(output)

        with open(self.get_name() + ".log", "w") as f:
            for output in total_output:
                f.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output):
        """Parse tool output and report issues."""
        xmllint_re = r"(.+):(\d+):\s(.+)\s:\s(.+)"
        parse = re.compile(xmllint_re)
        issues = []

        for output in total_output:
            for line in output.splitlines():
                match = parse.match(line)
                if match:
                    issues.append(Issue(match.group(1), match.group(2),
                                        self.get_name(), match.group(3), "5",
                                        match.group(4), None))

        return issues
