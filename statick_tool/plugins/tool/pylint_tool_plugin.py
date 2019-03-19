"""Apply pylint tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class PylintToolPlugin(ToolPlugin):
    """Apply pylint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "pylint"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = ["--msg-template='{abspath}:{line}: [{msg_id}({symbol}), "
                 "{obj}] {msg}'", "--reports=no"]
        flags += self.get_user_flags(level)

        total_output = []

        for src in package["python_src"]:
            try:
                subproc_args = ["pylint", src] + flags
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
                print("Couldn't find pylint executable! ({})".format(ex))
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
        pylint_re = r"(.+):(\d+):\s\[(.+)\]\s(.+)"
        parse = re.compile(pylint_re)
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
