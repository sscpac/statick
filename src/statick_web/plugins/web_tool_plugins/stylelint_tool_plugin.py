"""Apply stylelint tool and gather results."""

from __future__ import print_function

import json
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class StylelintToolPlugin(ToolPlugin):
    """Apply stylelint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "stylelint"

    def scan(self, package, level):  # pylint: disable=too-many-locals
        """Run tool and gather output."""
        tool_bin = "stylelint"

        tool_config = ".stylelintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags = []
        if format_file_name is not None:
            flags += ["--config", format_file_name]
        flags += ["-f", "json"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files = []
        if "html_src" in package:
            files += package["html_src"]
        if "css_src" in package:
            files += package["css_src"]

        total_output = []

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
                    print(
                        "{} failed! Returncode = {}".format(
                            tool_bin, str(ex.returncode)
                        )
                    )
                    print("{}".format(ex.output))
                    return None

            except OSError as ex:
                print("Couldn't find {}! ({})".format(tool_bin, ex))
                return None

        if self.plugin_context.args.show_tool_output:
            for output in total_output:
                print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            for output in total_output:
                f.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output):
        """Parse tool output and report issues."""
        issues = []

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
                    print("ValueError: {}".format(ex))

        return issues
