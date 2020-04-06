"""Apply htmllint tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class HTMLLintToolPlugin(ToolPlugin):
    """Apply HTML tidy tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "htmllint"

    def scan(self, package, level):  # pylint: disable=too-many-locals
        """Run tool and gather output."""
        tool_bin = "htmllint"

        tool_config = ".htmllintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags = []
        if format_file_name is not None:
            flags += ["--rc", format_file_name]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output = []

        for src in package["html_src"]:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                # tool returns 1 upon warnings and 2 upon errors
                if ex.returncode not in [1, 2]:
                    print(
                        "{} failed! Returncode = {}".format(
                            tool_bin, str(ex.returncode)
                        )
                    )
                    print("{}".format(ex.output))
                    return None

                total_output.append(ex.output)

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
        re_str = r"(.+):\s.+\s(\d+),\s.+,\s(.+)"
        parse = re.compile(re_str)
        issues = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                match = parse.match(line)
                if match:
                    filename = match.group(1)
                    line_number = match.group(2)
                    issue_type = "format"
                    severity = 3
                    message = match.group(3)
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
