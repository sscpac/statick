"""Apply writegood tool and gather results.

Website: https://github.com/btford/write-good
"""

import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class WriteGoodToolPlugin(ToolPlugin):  # type: ignore
    """Apply writegood tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "writegood"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["md_src", "rst_src"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        tool_bin = "write-good"

        flags: List[str] = ["--parse"]
        flags += user_flags

        total_output: List[str] = []

        try:
            exe = [tool_bin] + flags + files
            output = subprocess.check_output(
                exe, stderr=subprocess.STDOUT, universal_newlines=True
            )
            total_output.append(output)

        except subprocess.CalledProcessError as ex:
            if ex.returncode in (
                0,
                255,
            ):  # writegood returns 0 or 255 upon linting errors
                total_output.append(ex.output)
            else:
                logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        writegood_re = r"(.+):(\d+):(\d+):(.+)"
        parse: Pattern[str] = re.compile(writegood_re)
        issues: List[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            "suggestion",
                            "1",
                            match.group(4),
                            None,
                        )
                    )

        return issues
