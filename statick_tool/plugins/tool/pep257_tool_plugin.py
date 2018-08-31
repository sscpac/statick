"""Apply pep257 tool and gather results."""

from __future__ import print_function
import subprocess
import shlex
import re

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


class Pep257ToolPlugin(ToolPlugin):
    """Apply pep257 tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "pep257"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = []
        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = flags + list(lex)

        total_output = []

        for src in package["python_src"]:
            try:
                subproc_args = ["pep257", src] + flags
                output = subprocess.check_output(subproc_args,
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                if ex.returncode != 32:
                    output = ex.output
                else:
                    print("Problem {}".format(ex.returncode))
                    print("{}".format(ex.output))
                    return None

            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))

            total_output.append(output)

        with open(self.get_name() + ".log", "w") as fname:
            for output in total_output:
                fname.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output):
        """Parse tool output and report issues."""
        pep257_re_first = r"(.+):(\d+)"
        parse_first = re.compile(pep257_re_first)
        pep257_re_second = r"\s(.+):\s(.+)"
        parse_second = re.compile(pep257_re_second)
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
