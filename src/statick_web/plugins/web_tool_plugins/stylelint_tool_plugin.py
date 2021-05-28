"""Apply stylelint tool and gather results."""

import json
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class StylelintToolPlugin(ToolPlugin):  # type: ignore
    """Apply stylelint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "stylelint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "stylelint"

        tool_config = ".stylelintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = []
        if format_file_name is not None:
            flags += ["--config", format_file_name]
        flags += ["-f", "json"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: List[str] = []
        if "html_src" in package:
            files += package["html_src"]
        if "css_src" in package:
            files += package["css_src"]

        total_output: List[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output.strip())

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 2:  # returns 2 upon linting errors
                    total_output.append(ex.output.strip())
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
            logging.debug("%s", output)

        with open(self.get_name() + ".log", "w") as fid:
            for output in total_output:
                fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    # pylint: enable=too-many-locals

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                try:
                    err_dict = json.loads(line)[0]
                    for issue in err_dict["warnings"]:
                        severity_str = issue["severity"]
                        severity = 3
                        if severity_str == "warning":
                            severity = 3
                        elif severity_str == "error":
                            severity = 5
                        issues.append(
                            Issue(
                                err_dict["source"],
                                issue["line"],
                                self.get_name(),
                                issue["rule"],
                                severity,
                                issue["text"],
                                None,
                            )
                        )

                except ValueError as ex:
                    logging.warning("ValueError: %s", ex)

        return issues
