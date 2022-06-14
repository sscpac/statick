"""Apply xmllint tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class XmllintToolPlugin(ToolPlugin):
    """Apply xmllint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "xmllint"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["xml"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = []
        flags += user_flags

        total_output: List[str] = []

        for xml_file in files:
            try:
                subproc_args = ["xmllint", xml_file] + flags
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
                logging.warning("Couldn't find xmllint executable! (%s)", ex)
                return None

            logging.debug("%s", output)

            total_output.append(output)

        return total_output

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        xmllint_re = r"(.+):(\d+):\s(.+)\s:\s(.+)"
        parse: Pattern[str] = re.compile(xmllint_re)
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
                            match.group(3),
                            "5",
                            match.group(4),
                            None,
                        )
                    )

        return issues
