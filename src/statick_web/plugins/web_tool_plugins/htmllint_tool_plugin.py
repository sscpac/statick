"""Apply htmllint tool and gather results."""

import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class HTMLLintToolPlugin(ToolPlugin):  # type: ignore
    """Apply HTML tidy tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "htmllint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "htmllint"

        tool_config = ".htmllintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = []
        if format_file_name is not None:
            flags += ["--rc", format_file_name]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output: List[str] = []

        for src in package["html_src"]:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                # tool returns 1 upon warnings and 2 upon errors
                if ex.returncode not in [1, 2]:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

                total_output.append(ex.output)

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

        for output in total_output:
            logging.debug("%s", output)

        with open(self.get_name() + ".log", "w") as fid:
            for output in total_output:
                fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    # pylint: enable=too-many-locals

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        re_str = r"(.+):\s.+\s(\d+),\s.+,\s(.+)"
        parse: Pattern[str] = re.compile(re_str)
        issues: List[Issue] = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    filename = match.group(1)
                    line_number = match.group(2)
                    issue_type = "format"
                    severity = 3
                    message = match.group(3)
                    issues.append(
                        Issue(
                            filename,
                            line_number,
                            self.get_name(),
                            issue_type,
                            severity,
                            message,
                            None,
                        )
                    )
        return issues
