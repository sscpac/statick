"""Apply dockerfile-lint tool and gather results."""

import json
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DockerfileULintToolPlugin(ToolPlugin):  # type: ignore
    """Apply dockerfile-lint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "dockerfile-lint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        tool_bin = "dockerfile_lint"

        tool_config = "dockerfile_lint_rules.yaml"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = []
        if format_file_name is not None:
            flags += ["-r", format_file_name]
        flags += ["--json"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: List[str] = []
        if "dockerfile_src" in package:
            files += package["dockerfile_src"]

        total_output: List[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + ["-f", src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(self.add_filename(output, src))

            except subprocess.CalledProcessError as ex:
                # dockerfilelint returns the number of linting errors as the return code
                if ex.returncode > 0:
                    total_output.append(self.add_filename(ex.output, src))
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

    @classmethod
    def add_filename(cls, output: str, src: str) -> str:
        """Add the filename to the json output.

        This is because dockerfile-lint does not include the filename in the output.
        """
        try:
            json_dict = json.loads(output)
            json_dict["filename"] = src
            return json.dumps(json_dict)
        except ValueError as ex:
            logging.warning("ValueError: %s", ex)
            return output

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            try:
                err_dict = json.loads(output)
                for file_issues in [
                    err_dict["error"]["data"],
                    err_dict["warn"]["data"],
                    err_dict["info"]["data"],
                ]:
                    for issue in file_issues:
                        severity_str = issue["level"]
                        severity = "1"
                        if severity_str == "warn":
                            severity = "3"
                        elif severity_str == "error":
                            severity = "5"

                        message = issue["message"]
                        if "description" in issue:
                            message += ": " + issue["description"]

                        title = severity_str
                        if "line" in issue:
                            line = str(issue["line"])
                        else:
                            line = "-1"
                        if "label" in issue:
                            title = issue["label"]

                        issues.append(
                            Issue(
                                err_dict["filename"],
                                line,
                                self.get_name(),
                                title,
                                severity,
                                message,
                                None,
                            )
                        )

            except ValueError as ex:
                logging.warning("ValueError: %s", ex)
        # pylint: enable=too-many-nested-blocks
        return issues
