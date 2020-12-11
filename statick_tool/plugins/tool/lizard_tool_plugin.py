"""Apply lizard tool and gather results."""
import json
import re
import subprocess
import sys
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin

import lizard


class LizardToolPlugin(ToolPlugin):
    """Apply Lizard tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "lizard"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if not package.path:
            return []

        try:
            ## The following is basically copy-pasted from lizard.py's main() ##
            user_flags = [lizard.__file__] + self.get_user_flags(level) # leading None is required
            if '-w' not in user_flags:
                user_flags += ['-w']
            print('user_flags: {}'.format(user_flags))
            options = lizard.parse_args(user_flags)
            # print(options)
            printer = options.printer or lizard.print_result
            schema = lizard.OutputScheme(options.extensions)
            if schema.any_silent():
                printer = lizard.silent_printer
            schema.patch_for_extensions()
            if options.input_file:
                options.paths = lizard.auto_read(options.input_file).splitlines()
            original_stdout = sys.stdout
            output_file = None
            if options.output_file:
                output_file = lizard.open_output_file(options.output_file)
                sys.stdout = output_file
            print("\nLizard options: {}\n".format(options))
            # print('Lizard paths: {}'.format(options.paths))
            # print('Lizard directory: {}'.format(src_dir))
            print('options.printer: {}'.format(options.printer))
            print('options.paths: {}'.format(options.paths))
            print('options.exclude: {}'.format(options.exclude))
            print('options.extensions: {}'.format(options.extensions))
            print('options.languages: {}'.format(options.languages))
            result = lizard.analyze(
                options.paths,
                # src_dir,
                options.exclude,
                options.working_threads,
                options.extensions,
                options.languages)
            printer(result, options, schema, lizard.AllResult)
            lizard.print_extension_results(options.extensions)
            result = "".join(list(result))
            if output_file:
                sys.stdout = original_stdout
                output_file.close()

            # lizard output: /usr/src/gmock/src/gmock-spec-builders.cc:330: warning: testing::internal::GTEST_LOCK_EXCLUDED_ has 60 NLOC, 16 CCN, 414 token, 1 PARAM, 106 length
            print("Lizard result: {}".format(result))

        except OSError as ex:
            print("Couldn't find lizard executable! ({})".format(ex))
            return None

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(result))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                fid.write(output)

        issues = self.parse_output(result)
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
