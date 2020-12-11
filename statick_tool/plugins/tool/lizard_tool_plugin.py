"""Apply lizard tool and gather results."""
import os
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
            ## The following is a modification of lizard.py's main() ##
            user_flags = [lizard.__file__] + [package.path] + self.get_user_flags(level) # leading None is required
            # Make sure we log warnings
            if '-w' not in user_flags:
                user_flags += ['-w']
            
            # Create desired logging extension for later
            if ('-X' in user_flags) or ('--xml' in user_flags):
                log_extension = '.xml'
            elif '--csv' in user_flags:
                log_extension = '.csv'
            elif ('-H' in user_flags) or ('--html' in user_flags):
                log_extension = '.html'
            else:
                log_extension = '.log'

            # Make sure we log to a file for Statick
            if '-o' not in user_flags:
                log_file = self.get_name() + log_extension
                user_flags += ['-o', log_file]
            else:
                # Get the log file name
                log_file = user_flags[user_flags.index('-o') + 1]

            options = lizard.parse_args(user_flags)
            printer = options.printer or lizard.print_result
            schema = lizard.OutputScheme(options.extensions)
            if schema.any_silent():
                printer = lizard.silent_printer
            schema.patch_for_extensions()
            if options.input_file:
                options.paths = lizard.auto_read(options.input_file).splitlines()

            # Set up logging (sys.stdout now goes to file)
            original_stdout = sys.stdout
            output_file = lizard.open_output_file(options.output_file)
            sys.stdout = output_file

            result = lizard.analyze(
                options.paths,
                options.exclude,
                options.working_threads,
                options.extensions,
                options.languages)
            printer(result, options, schema, lizard.AllResult)
            lizard.print_extension_results(options.extensions)
            list(result)

            # Return to normal sys.stdout operation
            sys.stdout = original_stdout
            output_file.close()

            # Read back written data for the rest of Statick
            # There HAS to be a more elegant way to do this...
            if output_file:
                with open(log_file, 'r') as log_f:
                    output = "".join(log_f.readlines())

        except OSError as ex:
            print("Couldn't find lizard executable! ({})".format(ex))
            return None


        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        # Log file is already written at this point, so if we don't want it, delete it
        if not (self.plugin_context and self.plugin_context.args.output_directory):
           os.remove(log_file) 

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
