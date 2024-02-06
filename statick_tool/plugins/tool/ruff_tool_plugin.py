"""Apply ruff tool and gather results."""

import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class RuffToolPlugin(ToolPlugin):
    """Apply ruff tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "ruff"

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

        try:
            subproc_args = ["ruff"] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output

        except OSError as ex:
            logging.warning("Couldn't find ruff executable! (%s)", ex)
            return None

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []
        ruff_re = r"(.+):(\d+):(\d+):\s(.+)"
        parse: Pattern[str] = re.compile(ruff_re)

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issue_type = match.group(4).split()[0]
                    message = match.group(4).split(" ", 1)[1]
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            issue_type,
                            "5",
                            message,
                            None,
                        )
                    )

        return issues
