"""Apply pyflakes tool and gather results."""

from __future__ import print_function
import subprocess
import shlex
import re

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


class PyflakesToolPlugin(ToolPlugin):
    """Apply pyflakes tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "pyflakes"

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
                subproc_args = ["pyflakes", src] + flags
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
        pyflakes_re = r"(.+):(\d+):\s(.+)"
        parse = re.compile(pyflakes_re)
        issues = []

        for output in total_output:
            for line in output.split("\n"):
                match = parse.match(line)
                if match:
                    issues.append(Issue(match.group(1), match.group(2),
                                        self.get_name(), self.get_name(),
                                        "5", match.group(3), None))

        return issues
