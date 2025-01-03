"""Apply eslint tool and gather results."""

import json
import logging
import pathlib
import shutil
import subprocess
from typing import List, Optional, Tuple

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ESLintToolPlugin(ToolPlugin):  # type: ignore
    """Apply eslint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "eslint"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["html_src", "javascript_src"]

    def get_format_file(self, level: str) -> Tuple[str, bool]:
        """Retrieve format file path."""
        tool_config = "eslint.config.mjs"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        install_dir = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "install_dir"
        )
        copied_file = False
        if install_dir is not None:
            format_file_path = pathlib.Path(install_dir, tool_config).expanduser()

            if not format_file_path.exists():
                config_file_path = pathlib.Path(
                    self.plugin_context.resources.get_file(tool_config)
                )
                install_dir_path = pathlib.Path(install_dir).expanduser()
                logging.info(
                    "Copying eslint format file %s to: %s",
                    config_file_path,
                    install_dir_path,
                )
                shutil.copy(str(config_file_path), str(install_dir_path))
                copied_file = True

            format_file_name = str(format_file_path)
        else:
            format_file_name = self.plugin_context.resources.get_file(tool_config)

        return (format_file_name, copied_file)

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        tool_bin = "eslint"

        (format_file_name, copied_file) = self.get_format_file(level)

        flags: List[str] = ["-f", "json"]
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += []
        flags += user_flags

        total_output: List[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                if (
                    "Error: Cannot find module" in ex.output
                    or "Require stack:" in ex.output
                ):
                    # nodejs cannot find a module and threw an error
                    # this results in the same returncode `1` that eslint
                    # uses to indicate the presence of linting issues.
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

                if ex.returncode == 1:  # eslint returns 1 upon linting errors
                    total_output.append(ex.output)
                else:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    if copied_file:
                        self.remove_config_file(format_file_name)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                if copied_file:
                    self.remove_config_file(format_file_name)
                return None

        if copied_file:
            self.remove_config_file(format_file_name)

        return total_output

    # pylint: enable=too-many-locals

    @classmethod
    def remove_config_file(cls, format_file_name: str) -> None:
        """Remove config file automatically copied into directory."""
        format_file_path = pathlib.Path(format_file_name).expanduser()
        if format_file_path.exists():
            logging.info("Removing copied config file: %s", format_file_path)
            format_file_path.unlink()

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []
        for output in total_output:
            try:
                data = json.loads(output)
                for line in data:
                    file_path = line["filePath"]
                    for issue in line["messages"]:
                        severity_str = issue["severity"]
                        severity = 3
                        if severity_str == 1:  # warning
                            severity = 3
                        elif severity_str == 2:  # error
                            severity = 5
                        line_num = None
                        if "line" in issue:
                            line_num = issue["line"]
                        issues.append(
                            Issue(
                                file_path,
                                line_num,
                                self.get_name(),
                                issue["ruleId"],
                                severity,
                                issue["message"],
                                None,
                            )
                        )

            except json.JSONDecodeError as ex:
                logging.warning("JSONDecodeError: %s", ex)
            except ValueError as ex:
                logging.warning("ValueError: %s", ex)

        return issues
