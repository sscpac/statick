"""Apply catkin_lint tool and gather results."""
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CatkinLintToolPlugin(ToolPlugin):
    """Apply catkin_lint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "catkin_lint"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "catkin" not in package or not package["catkin"]:
            return []

        flags = []  # type: List[str]
        flags += self.get_user_flags(level)

        try:
            subproc_args = ["catkin_lint", package.path] + flags
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("catkin_lint failed! Returncode = {}".format(ex.returncode))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find catkin_lint executable! ({})".format(ex))
            return None

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fname:
                fname.write(output)

        issues = self.parse_output(package, output)
        return issues

    @classmethod
    def check_for_exceptions_has_file(cls, match: Match[str], package: Package) -> bool:
        """Manual exceptions."""
        message = match.group(5)
        norm_path = os.path.normpath(package.path + "/" + match.group(2))
        line = open(norm_path, "r").readlines()[int(match.group(3)) - 1].strip()

        # There are a few cases where this is ok.
        if message == "variable CMAKE_CXX_FLAGS is modified":
            if line == 'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x")':
                return True
            if line == 'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")':
                return True
        # There are a few cases where this is ok.
        elif message == "variable CMAKE_C_FLAGS is modified":
            if line == 'set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")':
                return True

        return False

    @classmethod
    def get_level(cls, issue_type: str) -> str:
        """Get level for given issue type."""
        if issue_type == "error":
            return "5"
        if issue_type == "warning":
            return "3"
        return "1"

    def parse_output(self, package: Package, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        lint_re = r"(.+):\s(.+)\((\d+)\):\s(.+):\s(.+)"
        lint2_re = r"(.+):\s(.+):\s(.+)"
        parse = re.compile(lint_re)  # type: Pattern[str]
        parse2 = re.compile(lint2_re)  # type: Pattern[str]

        issues = []
        for line in output.splitlines():
            match = parse.match(line)  # type: Optional[Match[str]]
            if match:
                if self.check_for_exceptions_has_file(match, package):
                    continue

                norm_path = os.path.normpath(package.path + "/" + match.group(2))

                issues.append(
                    Issue(
                        norm_path,
                        match.group(3),
                        self.get_name(),
                        match.group(4),
                        self.get_level(match.group(4)),
                        match.group(5),
                        None,
                    )
                )
            else:
                match2 = parse2.match(line)  # type: Optional[Match[str]]

                if match2:
                    norm_path = os.path.normpath(package.path + "/package.xml")

                    message = match2.group(3)
                    if message == "missing build_depend on 'rostest'":
                        message = "missing test_depend on 'rostest'"
                    elif message.startswith("unconfigured build_depend on"):
                        message += (
                            " (Make sure you aren't missing "
                            "COMPONENTS in find_package(catkin ...) "
                            "in CMakeLists.txt)"
                        )

                    message += (
                        " (I can't really tell if this applies for "
                        "package.xml or CMakeLists.txt. Make sure to "
                        "check both for this issue)"
                    )

                    issues.append(
                        Issue(
                            norm_path,
                            "1",
                            self.get_name(),
                            match2.group(2),
                            self.get_level(match2.group(2)),
                            message,
                            None,
                        )
                    )
        return issues
