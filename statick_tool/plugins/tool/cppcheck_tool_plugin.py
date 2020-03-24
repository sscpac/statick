"""Apply cppcheck tool and gather results."""
import argparse
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CppcheckToolPlugin(ToolPlugin):
    """Apply cppcheck tool and gather results."""

    # pylint: disable=super-init-not-called
    def __init__(self) -> None:
        """Initialize cppcheck extensions."""
        self.valid_extensions = [".h", ".hpp", ".c", ".cc", ".cpp", ".cxx"]

    # pylint: enable=super-init-not-called

    def get_name(self) -> str:
        """Get name of tool."""
        return "cppcheck"

    @classmethod
    def get_tool_dependencies(cls) -> List[str]:
        """Get a list of tools that must run before this one."""
        return ["make"]

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--cppcheck-bin", dest="cppcheck_bin", type=str, help="cppcheck binary path"
        )

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "make_targets" not in package and "headers" not in package:
            return []

        if self.plugin_context is None:
            return []

        flags = [
            "--report-progress",
            "--verbose",
            "--inline-suppr",
            "--language=c++",
            "--template=[{file}:{line}]: ({severity} {id}) {message}",
        ]
        flags += self.get_user_flags(level)
        user_version = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "version"
        )

        cppcheck_bin = "cppcheck"
        if self.plugin_context.args.cppcheck_bin is not None:
            cppcheck_bin = self.plugin_context.args.cppcheck_bin

        try:
            output = subprocess.check_output(
                [cppcheck_bin, "--version"],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            ver_re = r"(.+) ([0-9]*\.?[0-9]+)"
            parse = re.compile(ver_re)  # type: Pattern[str]
            match = parse.match(output)  # type: Optional[Match[str]]
            if match:
                ver = float(match.group(2))
                # If specific version is not specified just use the installed version.
                if user_version is not None and ver != float(user_version):
                    print(
                        "You need version {} of cppcheck, but you have {}. "
                        "See README.md for instuctions on how to install the "
                        "proper version".format(user_version, match.group(2))
                    )
                    return None
        except OSError as ex:
            print("Cppcheck not found! ({})".format(ex))
            return None

        files = []  # type: List[str]
        include_dirs = []  # type: List[str]
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
                if "include_dirs" in target:
                    for include_dir in target["include_dirs"]:
                        if include_dir not in include_dirs:
                            include_dirs.append(include_dir)
        if "headers" in package:
            files += package["headers"]

        if not files:
            return []

        include_args = []
        for include_dir in include_dirs:
            if package.path in include_dir:
                include_args.append("-I")
                include_args.append(include_dir)

        try:
            output = subprocess.check_output(
                [cppcheck_bin] + flags + include_args + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            print("cppcheck failed! Returncode = {}".format(ex.returncode))
            print("{}".format(ex.output))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fname:
                fname.write(output)

        issues = self.parse_output(output)
        return issues

    # pylint: enable=too-many-locals, too-many-branches, too-many-return-statements

    @classmethod
    def check_for_exceptions(cls, match: Match[str]) -> bool:
        """Manual exceptions."""
        # Sometimes you can't fix variableScope in old c code
        if match.group(1).endswith(".c") and match.group(4) == "variableScope":
            return True
        return False

    def parse_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        cppcheck_re = r"\[(.+):(\d+)\]:\s\((.+?)\s(.+?)\)\s(.+)"
        parse = re.compile(cppcheck_re)  # type: Pattern[str]
        issues = []
        warnings_mapping = self.load_mapping()
        for line in output.splitlines():
            match = parse.match(line)  # type: Optional[Match[str]]
            if (
                match
                and line[1] != "*"
                and match.group(3) != "information"
                and not self.check_for_exceptions(match)
            ):
                dummy, extension = os.path.splitext(match.group(1))
                if extension in self.valid_extensions:
                    cert_reference = None
                    if match.group(4) in warnings_mapping:
                        cert_reference = warnings_mapping[match.group(4)]
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            match.group(3) + "/" + match.group(4),
                            "5",
                            match.group(5),
                            cert_reference,
                        )
                    )
        return issues
