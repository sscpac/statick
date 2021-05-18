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

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "python_src" not in package:
            return []

        flags: List[str] = [
            "--show-absolute-path",
            "--show-error-codes",
            "--no-error-summary",
        ]
        user_flags = self.get_user_flags(level)
        flags += user_flags
        tool_bin = "mypy"
        total_output: List[str] = []

        for src in package["python_src"]:
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

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                for output in total_output:
                    fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements

    def parse_output(self, total_output: List[str]) -> List[Issue]:
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
