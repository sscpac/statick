"""Apply lacheck tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class LacheckToolPlugin(ToolPlugin):
    """Apply lacheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "lacheck"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan."""
        return ["tex"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output."""
        flags: list[str] = []
        flags += user_flags

        total_output: list[str] = []

        tool_bin = self.get_binary()
        try:
            subproc_args: list[str] = [tool_bin] + flags + files
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

        return total_output

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""
        tool_re: str = r"(.+)\s(.+)\s(\d+):\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: list[Issue] = []
        filename: str = ""
        line_number: int = 0
        issue_type: str = ""
        message: str = ""

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    filename = match.group(1)[1:-2]
                    issue_type = "lacheck"
                    line_number = int(match.group(3))
                    message = match.group(4)
                    issues.append(
                        Issue(
                            filename,
                            line_number,
                            self.get_name(),
                            issue_type,
                            3,
                            message,
                            None,
                        )
                    )

        return issues
