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

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["css_src", "html_src"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
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
        flags += user_flags

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

        return total_output

    # pylint: enable=too-many-locals

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
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
