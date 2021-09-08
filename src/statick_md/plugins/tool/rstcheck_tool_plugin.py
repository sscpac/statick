"""Apply rstcheck tool and gather results."""

import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class RstcheckToolPlugin(ToolPlugin):  # type: ignore
    """Apply rstcheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "rstcheck"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "rstcheck"

        flags: List[str] = []
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: List[str] = []
        if "rst_src" in package:
            files += package["rst_src"]

        total_output: List[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:  # markdownlint returns 1 upon linting errors
                    total_output.append(ex.output)
                else:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

        for output in total_output:
            logging.debug("%s", str(output))

        with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
            for output in total_output:
                fid.write(str(output))

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    # pylint: enable=too-many-locals

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        rstcheck_re = r"(.+):(\d+):\s\((.+)/(\d)\)\s(.+)"
        parse: Pattern[str] = re.compile(rstcheck_re)
        issues: List[Issue] = []

        for output in total_output:
            for line in output.split("\n"):
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            match.group(3),
                            match.group(4),
                            match.group(5),
                            None,
                        )
                    )
        return issues
