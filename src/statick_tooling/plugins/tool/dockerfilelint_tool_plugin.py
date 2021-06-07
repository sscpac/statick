"""Apply dockerfilelint tool and gather results."""

import json
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DockerfileLintToolPlugin(ToolPlugin):  # type: ignore
    """Apply dockerfilelint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "dockerfilelint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "dockerfilelint"

        tool_config = ".dockerfilelintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = []
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += ["-o", "json"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: List[str] = []
        if "dockerfile_src" in package:
            files += package["dockerfile_src"]

        total_output: List[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                # dockerfilelint returns the number of linting errors as the return code
                if ex.returncode > 0:
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

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            for line in output.split("\n"):
                if line:
                    try:
                        err_dict = json.loads(line)["files"]
                        for file_issues in err_dict:
                            for issue in file_issues["issues"]:
                                severity_str = issue["category"]
                                severity = "1"
                                if severity_str == "Possible Bug":
                                    severity = "3"
                                elif severity_str == "Deprecation":
                                    severity = "5"
                                issues.append(
                                    Issue(
                                        file_issues["file"],
                                        issue["line"],
                                        self.get_name(),
                                        issue["title"],
                                        severity,
                                        issue["description"],
                                        None,
                                    )
                                )

                    except ValueError as ex:
                        logging.warning("ValueError: %s, line: %s", ex, line)
        # pylint: enable=too-many-nested-blocks
        return issues
