"""Apply catkin_lint tool and gather results."""

from __future__ import print_function

import os
import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class CatkinLintToolPlugin(ToolPlugin):
    """Apply catkin_lint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "catkin_lint"

    def scan(self, package, level):
        """Run tool and gather output."""
        if "catkin" not in package or not package["catkin"]:
            return []
        flags = []
        flags += self.get_user_flags(level)

        try:
            subproc_args = ["catkin_lint", package.path] + flags
            output = subprocess.check_output(subproc_args,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("cpplint failed! Returncode = {}".format(ex.returncode))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find catkin_lint executable! (%s)" % (ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as fname:
            fname.write(output)

        issues = self.parse_output(package, output)
        return issues

    @classmethod
    def check_for_exceptions_has_file(cls, match, package):
        """Manual exceptions."""
        message = match.group(5)
        norm_path = os.path.normpath(package.path + "/" + match.group(2))
        line = open(norm_path, "r").readlines()[int(match.group(3)) - 1].strip()

        # There are a few cases where this is ok.
        if message == "variable CMAKE_CXX_FLAGS is modified":
            if line == 'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x")':
                return True
            elif line == 'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")':
                return True
        # There are a few cases where this is ok.
        elif message == "variable CMAKE_C_FLAGS is modified":
            if line == 'set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")':
                return True

        return False

    @classmethod
    def get_level(cls, issue_type):
        """Get level for given issue type."""
        if issue_type == "error":
            return "5"
        elif issue_type == "warning":
            return "3"
        else:
            return "1"

    def parse_output(self, package, output):
        """Parse tool output and report issues."""
        lint_re = r"(.+):\s(.+)\((\d+)\):\s(.+):\s(.+)"
        lint2_re = r"(.+):\s(.+):\s(.+)"
        parse = re.compile(lint_re)
        parse2 = re.compile(lint2_re)

        issues = []
        for line in output.split('\n'):
            match = parse.match(line)
            if match:
                if self.check_for_exceptions_has_file(match, package):
                    continue

                norm_path = os.path.normpath(package.path + "/" +
                                             match.group(2))

                issues.append(Issue(norm_path, match.group(3),
                                    self.get_name(), match.group(4),
                                    self.get_level(match.group(4)),
                                    match.group(5), None))
            else:
                match2 = parse2.match(line)

                if match2:
                    norm_path = os.path.normpath(package.path + "/package.xml")

                    message = match2.group(3)
                    if message == "missing build_depend on 'rostest'":
                        message = "missing test_depend on 'rostest'"
                    elif message.startswith("unconfigured build_depend on"):
                        message += " (Make sure you aren't missing " \
                                   "COMPONENTS in find_package(catkin ...) " \
                                   "in CMakeLists.txt)"

                    message += " (I can't really tell if this applies for " \
                               "package.xml or CMakeLists.txt. Make sure to " \
                               "check both for this issue)"

                    issues.append(Issue(norm_path, "1", self.get_name(),
                                        match2.group(2),
                                        self.get_level(match2.group(2)),
                                        message, None))
        return issues
