"""Apply jshint tool and gather results."""

import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class JSHintToolPlugin(ToolPlugin):  # type: ignore
    """Apply jshint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "jshint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "jshint"

        tool_config = ".jshintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = []
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += ["-e", ".js,.html", "--extract", "auto", "--reporter", "unix"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: List[str] = []
        if "html_src" in package:
            files += package["html_src"]
        if "javascript_src" in package:
            files += package["javascript_src"]

        total_output: List[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 2:  # jshint returns 2 upon linting errors
                    total_output.append(ex.output)
                else:
                    logging.warning(
                        "%s failed! Returncode = %s", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

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
        jshint_re = r"(.+):(\d+):(\d+):\s(.+)"
        parse: Pattern[str] = re.compile(jshint_re)
        issues: List[Issue] = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    filename = match.group(1)
                    line_number = match.group(2)
                    issue_type = "jshint"
                    severity = 5
                    message = match.group(4)
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
