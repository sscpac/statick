"""Apply docformatter tool and gather results."""
import logging
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DocformatterToolPlugin(ToolPlugin):
    """Apply docformatter tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "docformatter"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = ["-c"]
        flags += user_flags
        tool_bin = "docformatter"
        total_output: List[str] = []

        for src in files:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except (IOError, OSError) as ex:
                logging.warning("docformatter binary failed: %s", tool_bin)
                logging.warning("Error = %s", ex.strerror)
                return []

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 3:
                    total_output.append(ex.output)
                else:
                    logging.warning("docformatter binary failed: %s.", tool_bin)
                    logging.warning("Returncode: %d", ex.returncode)
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    continue

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    # pylint: enable=too-many-locals, too-many-branches, too-many-return-statements

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        # Gives relative path to file.
        tool_re = r"(.+)[\\/](.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: List[Issue] = []

        for output in total_output:
            lines = output.splitlines()
            for line in lines:
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            os.path.join(match.group(1), match.group(2)),
                            "0",
                            self.get_name(),
                            "format",
                            "3",
                            "would reformat",
                            None,
                        )
                    )
        return issues
