"""Apply lizard tool and gather results."""
import io
import re
from contextlib import redirect_stdout
from typing import List, Match, Optional, Pattern

import lizard

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin

DISABLED_FLAGS = ["-f", "--input_file", "-o", "--output_file", "-Edumpcomments"]


def _valid_flag(flag: str) -> bool:
    """Indicate if passed flag is invalid."""
    if flag in DISABLED_FLAGS:
        return False
    return True


def remove_invalid_flags(flag_list: List[str]) -> List[str]:
    """Filter out all flags in the DISABLED_FLAGS list."""
    return [x for x in flag_list if _valid_flag(x)]


class LizardToolPlugin(ToolPlugin):
    """Apply Lizard tool and gather results.

    NOTE: The `-f/--input_file`, `-o/--output_file`, and `-Edumpcomments` options are unsupported
    """

    def get_name(self) -> str:
        """Get name of tool."""
        return "lizard"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if not package.path:
            return []

        # The following is a modification of lizard.py's main() #
        raw_user_flags = (
            [lizard.__file__] + [package.path] + self.get_user_flags(level)
        )  # leading lizard file name is required

        # Make sure we log warnings
        if "-w" not in raw_user_flags:
            raw_user_flags += ["-w"]

        # Make sure unsupported arguments are not included
        user_flags = remove_invalid_flags(raw_user_flags)

        options = lizard.parse_args(user_flags)
        printer = options.printer or lizard.print_result
        schema = lizard.OutputScheme(options.extensions)
        schema.patch_for_extensions()

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

            if self.plugin_context:
                if self.plugin_context.args.show_tool_output:
                    print("{}".format(output))
                if self.plugin_context.args.output_directory:
                    with open(self.get_name() + ".log", "w") as fid:
                        fid.write(output)
        except OSError as ex:
            print("Error occurred while running lizard! ({})".format(ex))
            return None

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
