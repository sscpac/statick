"""Apply pycodestyle tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class PycodestyleToolPlugin(ToolPlugin):
    """Apply pycodestyle tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "pycodestyle"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = ["--format=pylint"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output = []

        tool_bin = "pycodestyle"
        for src in package["python_src"]:
            try:
                subproc_args = [tool_bin, src] + flags
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
                print("Couldn't find {}! ({})".format(tool_bin, ex))
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
        tool_re = r"(.+):(\d+):\s\[(.+)\]\s(.+)"
        parse = re.compile(tool_re)
        issues = []

        for output in total_output:
            for line in output.splitlines():
                match = parse.match(line)
                if match:
                    if "," in match.group(3):
                        parts = match.group(3).split(",")
                        if parts[1].strip() == "":
                            issues.append(Issue(match.group(1), match.group(2),
                                                self.get_name(), parts[0], "5",
                                                match.group(4), None))
                        else:
                            issues.append(Issue(match.group(1), match.group(2),
                                                self.get_name(), parts[0], "5",
                                                parts[1].strip() + ": " +
                                                match.group(4), None))
                    else:
                        issues.append(Issue(match.group(1), match.group(2),
                                            self.get_name(), match.group(3),
                                            "5", match.group(4), None))

        return issues
