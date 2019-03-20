"""Apply make tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class MakeToolPlugin(ToolPlugin):
    """Apply Make tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "make"

    def scan(self, package, level):
        """Run tool and gather output."""
        if "make_targets" not in package:
            return []

        extra_args = []
        output = None
        make_args = ["make", "statick_cmake_target"] + extra_args

        try:
            output = subprocess.check_output(["make", "clean"],
                                             universal_newlines=True)
            output = subprocess.check_output(make_args,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))
        except subprocess.CalledProcessError as ex:
            output = ex.output
            print("Make failed! Returncode = {}".format(ex.returncode))
            print("{}".format(ex.output))

        except OSError as ex:
            print("Couldn't find make executable! ({})".format(ex))
            return None

        with open(self.get_name() + ".log", "w") as fname:
            fname.write(output)

        issues = self.parse_output(package, output)
        return issues

    @classmethod
    def check_for_exceptions(cls, match):
        """Manual exceptions."""
        return match.group(4) == "note"

    @classmethod
    def filter_matches(cls, matches, package):
        """Filter matches."""
        i = 0
        result = []
        while i < len(matches):
            cur_match = matches[i]
            if "overloaded-virtual" in cur_match[4] and i + 1 < len(matches):
                next_match = matches[i + 1]
                if next_match[0].startswith(package.path):
                    result.append((next_match[0], next_match[1], next_match[2],
                                   cur_match[3], cur_match[4] + next_match[4]))
                i += 1  # Skip next match.
            else:
                result.append(cur_match)
            i += 1
        return result

    def parse_output(self, package, output):  # pylint: disable=too-many-locals, too-many-branches
        """Parse tool output and report issues."""
        make_re = r"(.+):(\d+):(\d+):\s(.+):\s(.+)"
        make_warning_re = r".*\[(.+)\].*"
        parse = re.compile(make_re)
        warning_parse = re.compile(make_warning_re)
        matches = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in output.splitlines():
            match = parse.match(line)
            if match and not self.check_for_exceptions(match):
                matches.append(match.groups())

        matches = self.filter_matches(matches, package)
        issues = []
        for match in matches:
            cert_reference = None
            warning_list = warning_parse.match(match[4])
            if warning_list is not None and warning_list.groups(1)[0] in warnings_mapping:
                cert_reference = warnings_mapping[warning_list.groups(1)[0]]

            if warning_list is None:
                # Something's gone wrong if we don't match the [warning] format
                if "fatal error" in match[3]:
                    warning_level = 5
                    category = "fatal-error"
                else:
                    category = "unknown-error"
            else:
                category = warning_list.groups(1)[0]

            if match[3].lower() == "warning":
                warning_level = 3
            elif match[3].lower() == "error":
                warning_level = 5
            elif match[3].lower() == "note":
                warning_level = 1
            else:
                warning_level = 3

            issue = Issue(match[0], match[1], self.get_name(), category, warning_level,
                          match[4], cert_reference)
            if issue not in issues:
                issues.append(issue)

        lines = output.splitlines()
        if "collect2: ld returned 1 exit status" in lines:
            issues.append(Issue("Linker", "0", self.get_name(), "linker", "5",
                                "Linking failed"))
        return issues
