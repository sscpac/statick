"""Apply pydocstyle tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PydocstyleToolPlugin(ToolPlugin):
    """Apply pydocstyle tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "pydocstyle"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = []
        flags += user_flags
        total_output = []

        tool_bin = "pydocstyle"
        for src in files:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                # Return code 1 just means "found problems"
                if ex.returncode != 1:
                    logging.warning("Problem %d", ex.returncode)
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

                output = ex.output

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

            logging.debug("%s: %s", src, output)

            total_output.append(output)

        return total_output

    def parse_output(  # pylint: disable=too-many-locals
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re = r"(.+):(\d+)"
        parse_first: Pattern[str] = re.compile(tool_re)
        tool_re_second = r"\s(.+):\s(.+)"
        parse_second: Pattern[str] = re.compile(tool_re_second)
        issues: List[Issue] = []
        filename = ""
        line_number = "0"
        issue_type = ""
        message = ""

        for output in total_output:
            first_line = True
            for line in output.splitlines():
                if first_line:
                    match: Optional[Match[str]] = parse_first.match(line)
                    first_line = False
                    if match:
                        filename = match.group(1)
                        line_number = match.group(2)
                else:
                    match_second: Optional[Match[str]] = parse_second.match(line)
                    first_line = True
                    if match_second:
                        issue_type = match_second.group(1)
                        message = match_second.group(2)
                        issues.append(
                            Issue(
                                filename,
                                line_number,
                                self.get_name(),
                                issue_type,
                                "5",
                                message,
                                None,
                            )
                        )

        return issues
