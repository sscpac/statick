"""Apply jshint tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class JSHintToolPlugin(ToolPlugin):
    """Apply jshint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "jshint"

    def scan(self, package, level):  # pylint: disable=too-many-locals
        """Run tool and gather output."""
        tool_bin = "jshint"

        tool_config = ".jshintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags = []
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += ["-e", ".js,.html", "--extract", "auto", "--reporter", "unix"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files = []
        if "html_src" in package:
            files += package["html_src"]
        if "javascript_src" in package:
            files += package["javascript_src"]

        total_output = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 2:  # jshint returns 2 upon linting errors
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
        jshint_re = r"(.+):(\d+):(\d+):\s(.+)"
        parse = re.compile(jshint_re)
        issues = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                match = parse.match(line)
                if match:
                    filename = match.group(1)
                    line_number = match.group(2)
                    issue_type = "jshint"
                    severity = 5
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
