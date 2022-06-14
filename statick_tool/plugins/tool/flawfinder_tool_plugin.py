"""Apply flawfinder tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class FlawfinderToolPlugin(ToolPlugin):
    """Apply flawfinder tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "flawfinder"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["c_src"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = ["--quiet", "-D", "--singleline"]
        flags += user_flags
        total_output: List[str] = []

        for src in files:
            try:
                subproc_args = ["flawfinder"] + flags + [src]
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )
            except subprocess.CalledProcessError as ex:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

            except OSError as ex:
                logging.warning("Couldn't find flawfinder executable! (%s)", ex)
                return None

            logging.debug("%s", output)

            total_output.append(output)

        return total_output

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        flawfinder_re = r"(.+):(\d+):\s+\[(\d+)\]\s+(.+):\s*(.+)"
        parse: Pattern[str] = re.compile(flawfinder_re)
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
                            match.group(4),
                            match.group(3),
                            match.group(5),
                            None,
                        )
                    )

        return issues
