"""Apply cmakelint tool and gather results."""
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CMakelintToolPlugin(ToolPlugin):
    """Apply cmakelint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "cmakelint"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "cmake" not in package or not package["cmake"]:
            # Package is not cmake!
            return []

        flags = []  # type: List[str]
        flags += self.get_user_flags(level)

        output = ""
        cmake_file = os.path.join(package.path, "CMakeLists.txt")

        try:
            subproc_args = ["cmakelint"] + flags + [cmake_file]
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            if ex.returncode == 1:
                output = ex.output
            else:
                print("Problem {}".format(ex.returncode))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find cmakelint executable! ({})".format(ex))
            return None

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as f:
                f.write(output)

        issues = self.parse_output(output)
        return issues

    def parse_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        cmakelint_re = r"(.+):(\d+):\s(.+)\s\[(.+)\]"
        parse = re.compile(cmakelint_re)  # type: Pattern[str]
        issues = []

        for line in output.splitlines():
            match = parse.match(line)  # type: Optional[Match[str]]
            if match:
                issue_type = match.group(4)
                if issue_type == "syntax":
                    level = "5"
                else:
                    level = "3"
                issues.append(
                    Issue(
                        match.group(1),
                        match.group(2),
                        self.get_name(),
                        match.group(4),
                        level,
                        match.group(3),
                        None,
                    )
                )

        return issues
