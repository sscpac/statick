"""Apply docformatter tool and gather results."""
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DocformatterToolPlugin(ToolPlugin):
    """Apply docformatter tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "docformatter"

    def scan(  # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
        self, package: Package, level: str
    ) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "python_src" not in package:
            return []

        flags = ["-c"]  # type: List[str]
        user_flags = self.get_user_flags(level)
        flags += user_flags
        tool_bin = "docformatter"
        total_output = []  # type: List[str]

        for src in package["python_src"]:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except (IOError, OSError) as ex:
                print("docformatter binary failed: {}".format(tool_bin))
                print("Error = {}".format(str(ex.strerror)))
                return []

            except subprocess.CalledProcessError as ex:
                print("docformatter binary failed: {}.".format(tool_bin))
                print("Returncode: {}".format(str(ex.returncode)))
                print("Error: {}".format(ex.output))
                total_output.append(ex.output)
                continue

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            for output in total_output:
                print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fname:
                for output in total_output:
                    fname.write(output)

        issues = self.parse_output(total_output)  # type: List[Issue]
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        # Gives relative path to file.
        tool_re = r"(.+)[\\/](.+)"
        parse = re.compile(tool_re)  # type: Pattern[str]
        issues = []

        for output in total_output:
            lines = output.splitlines()
            for line in lines:
                match = parse.match(line)  # type: Optional[Match[str]]
                if match:
                    issues.append(
                        Issue(
                            os.path.join(match.group(1), match.group(2)),
                            "0",
                            self.get_name(),
                            "format",
                            "3",
                            "docformatter",
                            None,
                        )
                    )
        return issues
