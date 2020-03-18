"""Apply lacheck tool and gather results."""

from __future__ import print_function

import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class LacheckToolPlugin(ToolPlugin):
    """Apply lacheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "lacheck"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags: List[str] = []
        user_flags: List[str] = self.get_user_flags(level)
        flags += user_flags
        total_output: List[str] = []

        tool_bin: str = "lacheck"
        for src in package["tex"]:
            try:
                subproc_args: List[str] = [tool_bin, src] + flags
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

            if self.plugin_context and self.plugin_context.args.show_tool_output:
                print("{}".format(output))

            total_output.append(output)

        with open(self.get_name() + ".log", "w") as fname:
            for output in total_output:
                fname.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re: str = r"(.+)\s(.+)\s(\d+):\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: List[Issue] = []
        filename: str = ''
        line_number: str = "0"
        issue_type: str = ''
        message: str = ''

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    filename = match.group(1)[1:-2]
                    issue_type = "lacheck"
                    line_number = match.group(3)
                    message = match.group(4)
                    issues.append(Issue(filename, line_number,
                                        self.get_name(), issue_type,
                                        "3", message, None))

        return issues
