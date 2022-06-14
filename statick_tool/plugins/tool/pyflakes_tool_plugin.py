"""Apply pyflakes tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PyflakesToolPlugin(ToolPlugin):
    """Apply pyflakes tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "pyflakes"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = []
        flags += user_flags

        total_output: List[str] = []

        for src in files:
            try:
                subproc_args = ["pyflakes", src] + flags
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
                logging.warning("Couldn't find pyflakes executable! (%s)", ex)
                return None

            logging.debug("%s: %s", src, output)

            total_output.append(output)
        return total_output

    def parse_output(  # pylint: disable=too-many-locals
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re_first = r"(.+):(\d+):(\d+):\s(.+)"
        parse_first: Pattern[str] = re.compile(tool_re_first)
        tool_re_second = r"(.+):(\d+):( \'.*?\'|'.*?')\s(.+)"
        parse_second: Pattern[str] = re.compile(tool_re_second)
        tool_re_third = r"(.+)"
        parse_third: Pattern[str] = re.compile(tool_re_third)
        tool_re_fourth = r"(.+):(\d+):(\d+)( \'.*?\'|'.*?')\s(.+)"
        parse_fourth: Pattern[str] = re.compile(tool_re_fourth)
        issues: List[Issue] = []
        filename = ""
        line_number = "0"
        issue_type = ""
        message = ""

        for output in total_output:  # pylint: disable=too-many-nested-blocks
            first_line = True
            found_match = False
            for line in output.splitlines():
                if first_line:
                    match: Optional[Match[str]] = parse_first.match(line)
                    first_line = False
                    if match:
                        found_match = True
                        filename = match.group(1)
                        line_number = match.group(2)
                        issue_type = match.group(4)
                    else:
                        match_second: Optional[Match[str]] = parse_second.match(line)
                        if match_second:
                            found_match = True
                            filename = match_second.group(1)
                            line_number = match_second.group(2)
                            issue_type = match_second.group(4)
                        else:
                            match_fourth: Optional[Match[str]] = parse_fourth.match(
                                line
                            )
                            if match_fourth:
                                found_match = True
                                filename = match_fourth.group(1)
                                line_number = match_fourth.group(2)
                                issue_type = match_fourth.group(5)
                else:
                    match_third: Optional[Match[str]] = parse_third.match(line)
                    first_line = True
                    if match_third:
                        found_match = True
                        message = match_third.group(1)
            if found_match:
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
