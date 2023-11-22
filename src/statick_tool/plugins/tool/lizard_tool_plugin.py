"""Apply lizard tool and gather results."""
import io
import logging
import re
from contextlib import redirect_stdout
from typing import List, Match, Optional, Pattern

import lizard

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class LizardToolPlugin(ToolPlugin):
    """Apply Lizard tool and gather results.

    Note: The `-f/--input_file`, `-o/--output_file`, and `-Edumpcomments`
    options are unsupported.
    """

    def get_name(self) -> str:
        """Get name of tool."""
        return "lizard"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if not package.path:
            return []

        # The following is a modification of lizard.py's main().
        raw_user_flags = (
            [lizard.__file__] + [package.path] + self.get_user_flags(level)
        )  # Leading lizard file name is required.

        # Make sure we log warnings.
        if "-w" not in raw_user_flags:
            raw_user_flags += ["-w"]

        # Make sure unsupported arguments are not included.
        user_flags = self.remove_invalid_flags(raw_user_flags)

        options = lizard.parse_args(user_flags)
        printer = options.printer or lizard.print_result
        schema = lizard.OutputScheme(options.extensions)
        schema.patch_for_extensions()

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

        logging.debug("%s", output)
        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                fid.write(output)

        issues: List[Issue] = self.parse_tool_output(output)

        return issues

    def parse_tool_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        lizard_re = r"(.+):(\d+):\s(.+):\s(.+)"
        parse: Pattern[str] = re.compile(lizard_re)
        matches = []
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match:
                matches.append(match.groups())

        issues: List[Issue] = []
        for item in matches:
            issue = Issue(
                item[0], item[1], self.get_name(), item[2], "5", item[3], None
            )
            if issue not in issues:
                issues.append(issue)

        return issues

    def remove_invalid_flags(self, flag_list: List[str]) -> List[str]:
        """Filter out all disabled flags."""
        return [x for x in flag_list if self.valid_flag(x)]

    @classmethod
    def valid_flag(cls, flag: str) -> bool:
        """Indicate if passed flag is invalid."""
        disabled_flags = ["-f", "--input_file", "-o", "--output_file", "-Edumpcomments"]
        if flag in disabled_flags:
            return False
        return True
