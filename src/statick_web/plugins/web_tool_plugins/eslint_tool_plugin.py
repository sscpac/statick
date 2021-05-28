"""Apply eslint tool and gather results."""

import logging
import pathlib
import re
import shutil
import subprocess
from typing import List, Match, Optional, Pattern, Tuple

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ESLintToolPlugin(ToolPlugin):  # type: ignore
    """Apply eslint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "eslint"

    def get_format_file(self, level: str) -> Tuple[str, bool]:
        """Retrieve format file path."""
        tool_config = ".eslintrc"
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
                shutil.copy(str(config_file_path), str(install_dir_path))
                copied_file = True

            format_file_name = str(format_file_path)
        else:
            format_file_name = self.plugin_context.resources.get_file(tool_config)

        return (format_file_name, copied_file)

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "eslint"

        (format_file_name, copied_file) = self.get_format_file(level)

        flags: List[str] = []
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += ["--ext", ".js,.html", "-f", "unix"]
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
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
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

        with open(self.get_name() + ".log", "w") as fid:
            for output in total_output:
                fid.write(output)
                logging.debug("%s", output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    # pylint: enable=too-many-locals

    @classmethod
    def remove_config_file(cls, format_file_name: str) -> None:
        """Remove config file automatically copied into directory."""
        format_file_path = pathlib.Path(format_file_name).expanduser()
        if format_file_path.exists():
            format_file_path.unlink()

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        eslint_re = r"(.+):(\d+):(\d+):\s(.+)\s\[(.+)\/(.+)\]"
        eslint_error_re = r"(.+):(\d+):(\d+):\s(.+):\s(.+)\s\[(.+)]"
        parse: Pattern[str] = re.compile(eslint_re)
        err_parse: Pattern[str] = re.compile(eslint_error_re)
        issues: List[Issue] = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                match: Optional[Match[str]] = parse.match(line)
                err_match: Optional[Match[str]] = err_parse.match(line)
                if match:
                    severity_str = match.group(5).lower()
                    severity = 3
                    if severity_str == "warning":
                        severity = 3
                    elif severity_str == "error":
                        severity = 5

                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            match.group(6),
                            severity,
                            match.group(4),
                            None,
                        )
                    )
                elif err_match:
                    severity_str = err_match.group(6).lower()
                    severity = 3
                    if severity_str == "error":
                        severity = 5

                    issues.append(
                        Issue(
                            err_match.group(1),
                            err_match.group(2),
                            self.get_name(),
                            err_match.group(4),
                            severity,
                            err_match.group(5),
                            None,
                        )
                    )
        return issues
