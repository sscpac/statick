"""Apply lizard tool and gather results."""
import io
import os
import re
import sys
from contextlib import redirect_stdout
from typing import List, Match, Optional, Pattern

import lizard

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class LizardToolPlugin(ToolPlugin):
    """Apply Lizard tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "lizard"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if not package.path:
            return []

        # The following is a modification of lizard.py's main() #
        user_flags = (
            [lizard.__file__] + [package.path] + self.get_user_flags(level)
        )  # leading lizard file name is required

        # Make sure we log warnings
        if "-w" not in user_flags:
            user_flags += ["-w"]

        options = lizard.parse_args(user_flags)
        printer = options.printer or lizard.print_result
        schema = lizard.OutputScheme(options.extensions)
        if schema.any_silent():
            printer = lizard.silent_printer
        schema.patch_for_extensions()
        if options.input_file:
            options.paths = lizard.auto_read(options.input_file).splitlines()

        if options.output_file:
            output_file = lizard.open_output_file(options.output_file)

        try:
            result = lizard.analyze(
                options.paths,
                options.exclude,
                options.working_threads,
                options.extensions,
                options.languages,
            )
            lizard_output = io.StringIO()
            with redirect_stdout(lizard_output):
                printer(result, options, schema, lizard.AllResult)
            output = lizard_output.getvalue()
            lizard.print_extension_results(options.extensions)
            list(result)

            if options.output_file:
                output_file.write(output)
                output_file.close()

        except OSError as ex:
            print("Error occurred while running lizard! ({})".format(ex))
            return None

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                fid.write(output)

        issues = self.parse_output(output)

        return issues

    def parse_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        lizard_re = r"(.+):(\d+):\s(.+):\s(.+)"
        parse = re.compile(lizard_re)  # type: Pattern[str]
        matches = []
        for line in output.splitlines():
            match = parse.match(line)  # type: Optional[Match[str]]
            if match:
                matches.append(match.groups())

        issues = []  # type: List[Issue]
        for item in matches:
            issue = Issue(
                item[0], item[1], self.get_name(), item[2], "5", item[3], None
            )
            if issue not in issues:
                issues.append(issue)

        return issues
