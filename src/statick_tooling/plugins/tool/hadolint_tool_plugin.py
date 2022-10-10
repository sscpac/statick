"""Apply hadolint tool and gather results."""

import argparse
import json
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class HadolintToolPlugin(ToolPlugin):  # type: ignore
    """Apply hadolint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "hadolint"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--hadolint-bin",
            dest="hadolint_bin",
            type=str,
            help="hadolint binary path",
        )
        args.add_argument(
            "--hadolint-docker",
            dest="hadolint_docker",
            action="store_true",
            help="Use hadolint docker image instead of binary",
        )

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["dockerfile_src"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        tool_bin = "hadolint"

        # If the user explicitly specifies a binary, let that override the default
        if self.plugin_context and self.plugin_context.args.hadolint_bin is not None:
            tool_bin = self.plugin_context.args.hadolint_bin

        tool_config = ".hadolint.yaml"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        config_file_path = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = ["-f", "json", "--no-fail"]
        if "-f" in user_flags:
            idx = user_flags.index("-f")
            logging.warning(
                "Statick requires hadolint to output in json format, "
                "ignoring user provided format: %s",
                user_flags[idx + 1],
            )
            user_flags.pop(idx)
            user_flags.pop(idx)
        flags += user_flags

        total_output: List[str] = []
        if (
            self.plugin_context
            and self.plugin_context.args.hadolint_docker is not None
            and self.plugin_context.args.hadolint_docker
        ):
            output = self.scan_docker(tool_bin, flags, files, config_file_path)
        else:
            if config_file_path is not None and config_file_path:
                flags += ["-c", config_file_path]
            output = self.scan_local_binary(tool_bin, flags, files)

        if output:
            total_output.append(output)
        else:
            return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    # pylint: enable=too-many-locals

    def scan_local_binary(
        self, tool_bin: str, flags: List[str], files: List[str]
    ) -> Optional[str]:
        """Use locally installed hadolint binary to scan."""
        try:
            exe = [tool_bin] + flags
            exe.extend(files)
            output = subprocess.check_output(
                exe, stderr=subprocess.STDOUT, universal_newlines=True
            )
            return output

        except subprocess.CalledProcessError as ex:
            logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

    def scan_docker(
        self, tool_bin: str, flags: List[str], files: List[str], config_file_path: str
    ) -> Optional[str]:
        """Use hadolint docker image to scan."""
        try:
            json_dict = []
            for src in files:
                exe = [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                ]
                if config_file_path is not None and config_file_path:
                    exe.extend(
                        [
                            "-v",
                            config_file_path + ":/.config/hadolint.yaml",
                        ]
                    )
                exe.extend(
                    [
                        "-v",
                        src + ":/Dockerfile",
                        "hadolint/hadolint",
                        "hadolint",
                    ]
                )
                exe.extend(flags)
                exe.append("Dockerfile")
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                if output:
                    output = output.replace(
                        '"file":"Dockerfile"', '"file":"' + src + '"'
                    )
                    try:
                        file_dict = json.loads(output)
                        for issue in file_dict:
                            json_dict.append(issue)
                    except json.decoder.JSONDecodeError as ex:
                        logging.error("Failed to decode json from %s, %s", output, ex)
                        return None
            return json.dumps(json_dict)

        except subprocess.CalledProcessError as ex:
            logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            for line in output.splitlines():
                if line:
                    try:
                        err_arr = json.loads(line)
                        for issue in err_arr:
                            severity_str = issue["level"]
                            severity = "1"
                            if severity_str == "style":
                                severity = "1"
                            elif severity_str == "info":
                                severity = "1"
                            elif severity_str == "warning":
                                severity = "3"
                            elif severity_str == "error":
                                severity = "5"
                            issues.append(
                                Issue(
                                    issue["file"],
                                    str(issue["line"]),
                                    self.get_name(),
                                    issue["code"],
                                    severity,
                                    issue["message"],
                                    None,
                                )
                            )

                    except ValueError as ex:
                        logging.warning("ValueError: %s, line: %s", ex, line)
        # pylint: enable=too-many-nested-blocks
        return issues
