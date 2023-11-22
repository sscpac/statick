"""Apply catkin_lint tool and gather results."""
import logging
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

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["catkin"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        flags: List[str] = []
        flags += user_flags

        try:
            subproc_args = ["catkin_lint", package.path] + flags
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("catkin_lint failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find catkin_lint executable! (%s)", ex)
            return None

        logging.debug("%s", output)
        return output.splitlines()

    @classmethod
    def check_for_exceptions_has_file(cls, match: Match[str], package: Package) -> bool:
        """Manual exceptions."""
        message = match.group(5)
        norm_path = os.path.normpath(package.path + "/" + match.group(2))
        with open(norm_path, "r", encoding="utf8") as fid:
            line = fid.readlines()[int(match.group(3)) - 1].strip()
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

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        lint_re = r"(.+):\s(.+)\((\d+)\):\s(.+):\s(.+)"
        lint2_re = r"(.+):\s(.+):\s(.+)"
        parse: Pattern[str] = re.compile(lint_re)
        parse2: Pattern[str] = re.compile(lint2_re)

        issues: List[Issue] = []
        for line in total_output:
            match: Optional[Match[str]] = parse.match(line)
            if match:
                if package is not None and self.check_for_exceptions_has_file(
                    match, package
                ):
                    continue

                if package is not None:
                    norm_path = os.path.normpath(package.path + "/" + match.group(2))
                else:
                    norm_path = os.path.normpath(match.group(2))

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
                match2: Optional[Match[str]] = parse2.match(line)

                if match2:
                    if package is not None:
                        norm_path = os.path.normpath(package.path + "/package.xml")
                    else:
                        norm_path = os.path.normpath("package.xml")

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
