"""Apply lacheck tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class LacheckToolPlugin(ToolPlugin):  # type: ignore
    """Apply lacheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "lacheck"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags = []  # type: List[str]
        user_flags = self.get_user_flags(level)  # type: List[str]
        flags += user_flags
        total_output = []  # type: List[str]

        tool_bin = "lacheck"  # type: str
        for src in package["tex"]:
            try:
                subproc_args = [tool_bin, src] + flags  # type: List[str]
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

            logging.debug("%s", output)

            total_output.append(output)

        with open(self.get_name() + ".log", "w", encoding="utf-8") as fid:
            for output in total_output:
                fid.write(output)

        issues = self.parse_output(total_output)  # type: List[Issue]
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re = r"(.+)\s(.+)\s(\d+):\s(.+)"  # type: str
        parse = re.compile(tool_re)  # type: Pattern[str]
        issues = []  # type: List[Issue]
        filename = ""  # type: str
        line_number = "0"  # type: str
        issue_type = ""  # type: str
        message = ""  # type: str

        for output in total_output:
            for line in output.splitlines():
                match = parse.match(line)  # type: Optional[Match[str]]
                if match:
                    filename = match.group(1)[1:-2]
                    issue_type = "lacheck"
                    line_number = match.group(3)
                    message = match.group(4)
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
