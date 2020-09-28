"""Apply black tool and gather results."""
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class BlackToolPlugin(ToolPlugin):
    """Apply black tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "black"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags = ["--check"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output = []

        tool_bin = "black"
        for src in package["python_src"]:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                # Return code 123 means there was an internal error
                if ex.returncode == 123:
                    print("Black encountered internal error")
                    print("{}".format(ex.output))

                # Return code 1 just means "found problems"
                elif ex.returncode != 1:
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

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fname:
                for output in total_output:
                    fname.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re_reformat = r"(.+)\s(.+)\s(.+)"
        parse_reformat = re.compile(tool_re_reformat)  # type: Pattern[str]
        tool_re_error = r"\w+:\s(.+):\s(.+):\s(.+):\s(.+)"
        parse_error = re.compile(tool_re_error)  # type: Pattern[str]
        issues = []

        for output in total_output:
            for line in output.splitlines():
                if line.startswith("would reformat"):
                    match = parse_reformat.match(line)  # type: Optional[Match[str]]
                    if match:
                        issues.append(
                            Issue(
                                match.group(3),
                                "0",
                                self.get_name(),
                                "format",
                                "3",
                                "would reformat",
                                None,
                            )
                        )
                if line.startswith("error"):
                    match_error = parse_error.match(line)  # type: Optional[Match[str]]
                    if match_error:
                        issues.append(
                            Issue(
                                match_error.group(1).split(" ")[2],
                                "0",
                                self.get_name(),
                                "format",
                                "3",
                                match_error.group(3),
                                None,
                            )
                        )

        return issues
