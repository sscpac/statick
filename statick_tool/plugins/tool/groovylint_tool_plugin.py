"""Apply GroovyLint tool and gather results."""

import json
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class GroovyLintToolPlugin(ToolPlugin):
    """Apply GroovyLint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "groovylint"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["groovy_src"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        tool_bin = "npm-groovy-lint"

        tool_config = ".groovylintrc.json"
        if self.plugin_context:
            user_config = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "config"
            )
        if user_config is not None:
            tool_config = user_config
        if self.plugin_context:
            format_file_name = self.plugin_context.resources.get_file(tool_config)

        flags: List[str] = []
        if format_file_name is not None:
            flags += ["--config", format_file_name]
        flags += ["--serverhost", "http://127.0.0.1"]
        flags += ["--serverport", "7484"]
        flags += ["--output", "json"]
        flags += user_flags

        total_output: List[str] = []
        for src in files:
            try:
                exe = [tool_bin] + flags + ["-f", src]
                output = subprocess.check_output(
                    exe,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=package.path,
                )
                total_output.append(output)
            except subprocess.CalledProcessError as ex:
                # npm-groovy-lint returns 1 on some errors but still has valid output
                if ex.returncode == 1:
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
        return total_output

    # pylint: enable=too-many-locals

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                try:
                    err_dict = json.loads(line)
                    if "files" in err_dict:
                        all_files = err_dict["files"]
                        for file_name in all_files:
                            file_errs = all_files[file_name]
                            if "errors" in file_errs:
                                for issue in file_errs["errors"]:
                                    severity_str = issue["severity"]
                                    severity = "3"
                                    if severity_str == "info":
                                        severity = "1"
                                    elif severity_str == "warning":
                                        severity = "3"
                                    elif severity_str == "error":
                                        severity = "5"
                                    issues.append(
                                        Issue(
                                            file_name,
                                            str(issue["line"]),
                                            self.get_name(),
                                            issue["rule"],
                                            severity,
                                            issue["msg"],
                                            None,
                                        )
                                    )

                except ValueError as ex:
                    logging.warning("ValueError: %s", ex)
        # pylint: enable=too-many-nested-blocks
        return issues
