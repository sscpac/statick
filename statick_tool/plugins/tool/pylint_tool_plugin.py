"""Apply pylint tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PylintToolPlugin(ToolPlugin):
    """Apply pylint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "pylint"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = [
            "--msg-template='{abspath}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
            "--reports=no",
        ]
        flags += user_flags

        total_output: List[str] = []

        for src in files:
            try:
                subproc_args = ["pylint", src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                if ex.returncode != 32:
                    output = ex.output
                else:
                    logging.warning("Problem %d", ex.returncode)
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find pylint executable! (%s)", ex)
                return None

            logging.debug("%s: %s", src, output)

            total_output.append(output)

        return total_output

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        pylint_re = r"(.+):(\d+):\s\[(.+)\]\s(.+)"
        parse: Pattern[str] = re.compile(pylint_re)
        issues: List[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    if "," in match.group(3):
                        parts = match.group(3).split(",")
                        if parts[1].strip() == "":
                            issues.append(
                                Issue(
                                    match.group(1),
                                    match.group(2),
                                    self.get_name(),
                                    parts[0],
                                    "5",
                                    match.group(4),
                                    None,
                                )
                            )
                        else:
                            issues.append(
                                Issue(
                                    match.group(1),
                                    match.group(2),
                                    self.get_name(),
                                    parts[0],
                                    "5",
                                    parts[1].strip() + ": " + match.group(4),
                                    None,
                                )
                            )
                    else:
                        issues.append(
                            Issue(
                                match.group(1),
                                match.group(2),
                                self.get_name(),
                                match.group(3),
                                "5",
                                match.group(4),
                                None,
                            )
                        )

        return issues
