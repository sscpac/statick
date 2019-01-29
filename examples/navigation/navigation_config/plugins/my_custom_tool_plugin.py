"""Run grep."""

from __future__ import print_function

import re
import shlex
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class MyCustomToolPlugin(ToolPlugin):
    """Run grep."""

    @classmethod
    def get_name(cls):
        """Get name of tool."""
        return "my_custom_tool"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = ["-rn"]
        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = flags + list(lex)

        output = None

        try:
            subproc_args = ["grep"] + flags + [package.path]
            output = subprocess.check_output(subproc_args,
                                             stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as ex:
            print("Problem {}".format(ex.returncode))
            print("{}".format(ex.output))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as fname:
            fname.write(output)

        issues = self.parse_output(output)
        return issues

    def parse_output(self, output):
        """Parse tool output and report issues."""
        grep_re = r"(.+):(\d+):(.+)"
        parse = re.compile(grep_re)
        issues = []

        for line in output.split("\n"):
            match = parse.match(line)
            if match:
                issues.append(Issue(match.group(1), match.group(2),
                                    self.get_name(), "banned_pattern", "5",
                                    "Banned pattern found: " + match.group(3)))

        return issues
