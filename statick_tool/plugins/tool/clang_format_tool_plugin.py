"""Apply clang-format tool and gather results."""
import argparse
import difflib
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ClangFormatToolPlugin(ToolPlugin):
    """Apply clang-format tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "clang-format"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--clang-format-bin",
            dest="clang_format_bin",
            type=str,
            help="clang-format binary path",
        )
        args.add_argument(
            "--clang-format-raise-exception",
            dest="clang_format_raise_exception",
            action="store_true",
            help="clang-format raise exception on mismatched " "configuration file",
        )
        args.add_argument(
            "--clang-format-ignore-exception",
            dest="clang_format_raise_exception",
            action="store_false",
            help="clang-format ignore exception on mismatched " "configuration file",
        )
        args.set_defaults(clang_format_raise_exception=True)

    def scan(
        self, package: Package, level: str
    ) -> Optional[
        List[Issue]
    ]:  # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
        """Run tool and gather output."""
        if "make_targets" not in package and "headers" not in package:
            return []

        user_version = None
        if self.plugin_context:
            user_version = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "version"
            )

        clang_format_bin = "clang-format"
        if user_version is not None:
            clang_format_bin = "{}-{}".format(clang_format_bin, user_version)

        # If the user explicitly specifies a binary, let that override the user_version
        if (
            self.plugin_context
            and self.plugin_context.args.clang_format_bin is not None
        ):
            clang_format_bin = self.plugin_context.args.clang_format_bin

        files = []  # type: List[str]
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
        if "headers" in package:
            files += package["headers"]

        check = self.check_configuration(clang_format_bin)  # type: Optional[bool]
        if check is None:
            return None
        if not check:
            return []

        total_output = []  # type: List[str]

        try:
            for src in files:
                output = subprocess.check_output(
                    [clang_format_bin, src, "-output-replacements-xml"],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
                output = src + "\n" + output
                if (
                    self.plugin_context
                    and self.plugin_context.args.clang_format_raise_exception
                ):
                    total_output.append(output)

        except (IOError, OSError) as ex:
            print("clang-format binary failed: {}".format(clang_format_bin))
            print("Error = {}".format(str(ex.strerror)))
            if (
                self.plugin_context
                and self.plugin_context.args.clang_format_raise_exception
            ):
                return None
            return []

        except subprocess.CalledProcessError as ex:
            print("clang-format binary failed: {}.".format(clang_format_bin))
            print("Returncode: {}".format(str(ex.returncode)))
            print("Error: {}".format(ex.output))
            if (
                self.plugin_context
                and self.plugin_context.args.clang_format_raise_exception
            ):
                return None
            return []

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            for output in total_output:
                print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fname:
                for output in total_output:
                    fname.write(output)

        issues = self.parse_output(total_output)  # type: List[Issue]
        return issues

    def check_configuration(self, clang_format_bin: str) -> Optional[bool]:
        """Check that configuration is configured properly."""
        if self.plugin_context is None:
            return False

        try:
            default_file_name = "_clang-format"
            format_file_name = self.plugin_context.resources.get_file(default_file_name)
            exc_msg = (
                "_clang-format style is not correct. There is one located in {}. "
                "Put this file in your home directory.".format(format_file_name)
            )

            with open(
                os.path.expanduser("~/" + default_file_name), "r"
            ) as home_format_file, open(
                format_file_name, "r"  # type: ignore
            ) as format_file:
                actual_format = home_format_file.read()
                target_format = format_file.read()
            diff = difflib.context_diff(
                actual_format.splitlines(), target_format.splitlines()
            )
            for line in diff:
                if (
                    line.startswith("+ ")
                    or line.startswith("- ")
                    or line.startswith("! ")
                ) and len(line) > 2:
                    if line[2:].strip() and line[2:].strip()[0] != "#":
                        exc = subprocess.CalledProcessError(
                            -1, clang_format_bin, exc_msg
                        )
                        if self.plugin_context.args.clang_format_raise_exception:
                            raise exc

        except (IOError, OSError) as ex:
            print("{}".format(exc_msg))
            print("Error: {}".format(str(ex.strerror)))
            if self.plugin_context.args.clang_format_raise_exception:
                return None
            return False

        except subprocess.CalledProcessError as ex:
            print("{} Returncode = {}".format(exc_msg, str(ex.returncode)))
            if self.plugin_context.args.clang_format_raise_exception:
                return None

        return True

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        clangformat_re = r"<replacement offset="
        parse = re.compile(clangformat_re)  # type: Pattern[str]
        issues = []

        for output in total_output:
            lines = output.splitlines()
            filename = lines[0]
            count = 0
            for line in lines:
                match = parse.match(line)  # type: Optional[Match[str]]
                if match:
                    count += 1
            if count > 0:
                issues.append(
                    Issue(
                        filename,
                        "0",
                        self.get_name(),
                        "format",
                        "1",
                        str(count) + " replacements",
                        None,
                    )
                )
        return issues
