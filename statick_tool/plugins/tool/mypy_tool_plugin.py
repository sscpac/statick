"""Apply mypy tool and gather results."""
import logging
import re
import subprocess
import sys
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class MypyToolPlugin(ToolPlugin):
    """Apply mypy tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "mypy"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = [
            "--show-absolute-path",
            "--show-error-codes",
            "--no-error-summary",
        ]
        flags += user_flags
        tool_bin = "mypy"
        total_output: List[str] = []

        for src in files:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except (IOError, OSError) as ex:
                logging.warning("mypy binary failed: %s", tool_bin)
                logging.warning("Error = %s", ex.strerror)
                return []

            except subprocess.CalledProcessError as ex:
                logging.warning("mypy binary failed: %s.", tool_bin)
                logging.warning("Returncode: %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                total_output.append(ex.output)
                continue

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        # file:line: severity: msg type
        tool_re = r"(.+):(\d+):\s(.+):\s(.+)\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: List[Issue] = []

        for output in total_output:
            lines = output.splitlines()
            for line in lines:
                if sys.platform != "win32" and not line.startswith("/"):
                    continue
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issue_type = match.group(5).strip("[]")
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            issue_type,
                            "5",
                            match.group(4),
                            None,
                        )
                    )
        return issues
