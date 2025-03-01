"""Apply xmllint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class XmllintToolPlugin(ToolPlugin):
    """Apply xmllint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "xmllint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan."""
        return ["xml"]

    def get_binary(self) -> str:
        """Get tool binary name."""
        return "xmllint"

    def get_version_re(self) -> str:
        """Return regular expression to parse output for version number."""
        return r"(.*) ([0-9]*\.?[0-9]+\.?[0-9]+)"

    def process_version(self, output) -> str:
        version = "Unknown"
        ver_re = self.get_version_re()
        parse: Pattern[str] = re.compile(ver_re)
        match: Optional[Match[str]] = parse.match(output)
        if match:
            version = match.group(self.get_version_match_group())
        return version

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output."""
        flags: list[str] = []
        flags += user_flags
        tool_bin = self.get_binary()

        total_output: list[str] = []

        try:
            subproc_args = [tool_bin] + flags + files
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

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""
        xmllint_re = r"(.+):(\d+):\s(.+)\s:\s(.+)"
        parse: Pattern[str] = re.compile(xmllint_re)
        issues: list[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            match.group(1),
                            int(match.group(2)),
                            self.get_name(),
                            match.group(3),
                            5,
                            match.group(4),
                            None,
                        )
                    )

        return issues
