"""Apply chktex tool and gather results.

Chktex documentation at http://mirrors.rit.edu/CTAN/systems/doc/chktex/ChkTeX.pdf.
"""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ChktexToolPlugin(ToolPlugin):  # type: ignore
    """Apply chktex tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "chktex"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags: List[str] = []
        user_flags: List[str] = self.get_user_flags(level)
        flags += user_flags
        total_output: List[str] = []

        tool_bin: str = "chktex"
        for src in package["tex"]:
            try:
                subproc_args: List[str] = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                # Return code 1 means "found problems".
                # Return code 2 provides correct output with test cases used so far.
                if ex.returncode not in (1, 2):
                    logging.warning("Problem %s", ex.returncode)
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None
                output = ex.output

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

            logging.debug("%s", output)

            total_output.append(output)

        with open(self.get_name() + ".log", "w", encoding="utf-8") as fid:
            for output in total_output:
                fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re: str = r"(.+)\s(\d+)\s(.+)\s(.+)\s(.+)\s(\d+):\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: List[Issue] = []
        filename: str = ""
        line_number: str = "0"
        issue_type: str = ""
        message: str = ""

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    if match.group(1) == "Warning":
                        filename = match.group(4)
                        issue_type = match.group(2)
                        line_number = match.group(6)
                        message = match.group(7)
                        issues.append(
                            Issue(
                                filename,
                                line_number,
                                self.get_name(),
                                issue_type,
                                "3",
                                message,
                                None,
                            )
                        )

        return issues
