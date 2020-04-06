"""Apply markdownlint tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class MarkdownlintToolPlugin(ToolPlugin):
    """Apply markdownlint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "markdownlint"

    def scan(self, package, level):  # pylint: disable=too-many-locals
        """Run tool and gather output."""
        tool_bin = "markdownlint"

        tool_config = ".markdownlintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags = []
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files = []
        if "md_src" in package:
            files += package["md_src"]

        total_output = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:  # markdownlint returns 1 upon linting errors
                    total_output.append(ex.output)
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
        markdownlint_re = r"(.+):(\d+)\s([^\s]+)\s(.+)"
        markdownlint_re_with_col = r"(.+):(\d+):(\d+)\s([^\s]+)\s(.+)"
        parse = re.compile(markdownlint_re)
        parse_with_col = re.compile(markdownlint_re_with_col)
        issues = []

        for output in total_output:
            for line in output.split("\n"):
                match = parse_with_col.match(line)
                if match:
                    filename = match.group(1)
                    line_number = match.group(2)
                    issue_type = match.group(4)
                    severity = 3
                    message = match.group(5)
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
                else:
                    match = parse.match(line)
                    if match:
                        filename = match.group(1)
                        line_number = match.group(2)
                        issue_type = match.group(3)
                        severity = 3
                        message = match.group(4)
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
