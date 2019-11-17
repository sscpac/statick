"""Apply pyflakes tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class PyflakesToolPlugin(ToolPlugin):
    """Apply pyflakes tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "pyflakes"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = []
        flags += self.get_user_flags(level)

        total_output = []

        for src in package["python_src"]:
            try:
                subproc_args = ["pyflakes", src] + flags
                output = subprocess.check_output(subproc_args,
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)

            except subprocess.CalledProcessError as ex:
                # Return code 1 just means "found problems"
                if ex.returncode != 1:
                    print("Problem {}".format(ex.returncode))
                    print("{}".format(ex.output))
                    return None

                output = ex.output

            except OSError as ex:
                print("Couldn't find pyflakes executable! ({})".format(ex))
                return None

            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))

            total_output.append(output)

        with open(self.get_name() + ".log", "w") as fname:
            for output in total_output:
                fname.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output):  # pylint: disable=too-many-locals
        """Parse tool output and report issues."""
        tool_re_first = r"(.+):(\d+):(\d+):\s(.+)"
        parse_first = re.compile(tool_re_first)
        tool_re_second = r"(.+):(\d+):\s(.+)"
        parse_second = re.compile(tool_re_second)
        tool_re_third = r"\s(.+)"
        parse_third = re.compile(tool_re_third)
        issues = []
        filename = ''
        line_number = 0
        issue_type = ''
        message = ''

        for output in total_output:
            first_line = True
            found_match = False
            for line in output.splitlines():
                if first_line:
                    match = parse_first.match(line)
                    first_line = False
                    if match:
                        found_match = True
                        filename = match.group(1)
                        line_number = match.group(2)
                        issue_type = match.group(4)
                    else:
                        match = parse_second.match(line)
                        if match:
                            found_match = True
                            filename = match.group(1)
                            line_number = match.group(2)
                            issue_type = match.group(3)
                else:
                    match = parse_third.match(line)
                    first_line = True
                    if match:
                        found_match = True
                        message = match.group(1)
            if found_match:
                issues.append(Issue(filename, line_number,
                                    self.get_name(), issue_type,
                                    "5", message, None))

        return issues
