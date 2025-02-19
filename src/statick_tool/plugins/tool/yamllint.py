"""Apply yamllint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class YamllintToolPlugin(ToolPlugin):
    """Apply yamllint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "yamllint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan."""
        return ["yaml"]

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output."""
        flags: list[str] = ["-f", "parsable"]
        flags += user_flags

        total_output: list[str] = []
        output: str = ""

        try:
            subproc_args = ["yamllint"] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            if ex.returncode == 1:
                output = ex.output
            else:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find yamllint executable! (%s)", ex)
            return None

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""
        yamllint_re = r"(.+):(\d+):(\d+):\s\[(.+)\]\s(.+)\s\((.+)\)"
        parse: Pattern[str] = re.compile(yamllint_re)
        issues: list[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issue_type = match.group(4)
                    severity = 3
                    if issue_type == "error":
                        severity = 5
                    issues.append(
                        Issue(
                            match.group(1),
                            int(match.group(2)),
                            self.get_name(),
                            match.group(6),
                            severity,
                            match.group(5),
                            None,
                        )
                    )

        return issues
