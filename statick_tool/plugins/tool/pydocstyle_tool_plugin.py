"""Apply pydocstyle tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class PydocstyleToolPlugin(ToolPlugin):
    """Apply pydocstyle tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "pydocstyle"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = []
        user_flags = self.get_user_flags(level)
        # This check is done to support the switch from the pep257 package name
        # to the pydocstyle package name. See:
        # https://github.com/PyCQA/pydocstyle/issues/172
        # We want to support the old tool name in configuration files for a
        # while.
        if user_flags is None:
            user_flags = self.get_user_flags(level, "pep257")
            if user_flags is not None:
                print("DEPRECATION WARNING: The tool name changed from pep257 to "
                      "pydocstyle. Please update your configuration file to "
                      "use the new tool name.")
        flags += user_flags
        total_output = []

        tool_bin = "pydocstyle"
        for src in package["python_src"]:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(subproc_args,
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)

            except subprocess.CalledProcessError as ex:
                if ex.returncode != 32:
                    output = ex.output
                else:
                    print("Problem {}".format(ex.returncode))
                    print("{}".format(ex.output))
                    return None

            except OSError as ex:
                print("Couldn't find %s! (%s)" % (tool_bin, ex))
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
        tool_re = r"(.+):(\d+)"
        parse_first = re.compile(tool_re)
        tool_re_second = r"\s(.+):\s(.+)"
        parse_second = re.compile(tool_re_second)
        issues = []
        filename = ''
        line_number = 0
        issue_type = ''
        message = ''

        for output in total_output:
            first_line = True
            for line in output.split("\n"):
                if first_line:
                    match = parse_first.match(line)
                    first_line = False
                    if match:
                        filename = match.group(1)
                        line_number = match.group(2)
                else:
                    match = parse_second.match(line)
                    first_line = True
                    if match:
                        issue_type = match.group(1)
                        message = match.group(2)
                        issues.append(Issue(filename, line_number,
                                            self.get_name(), issue_type,
                                            "5", message, None))

        return issues
