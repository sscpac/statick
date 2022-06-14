"""Apply clang-tidy tool and gather results."""
import argparse
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ClangTidyToolPlugin(ToolPlugin):
    """Apply clang-tidy tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "clang-tidy"

    @classmethod
    def get_tool_dependencies(cls) -> List[str]:
        """Get a list of tools that must run before this one."""
        return ["make"]

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--clang-tidy-bin",
            dest="clang_tidy_bin",
            type=str,
            help="clang-tidy binary path",
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if (
            "make_targets" not in package
            or "src_dir" not in package
            or "bin_dir" not in package
        ):
            return []

        if self.plugin_context is None:
            return []

        clang_tidy_bin = "clang-tidy"

        user_version = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "version"
        )

        if user_version is not None:
            clang_tidy_bin = f"{clang_tidy_bin}-{user_version}"

        # If the user explicitly specifies a binary, let that override the user_version
        if self.plugin_context.args.clang_tidy_bin is not None:
            clang_tidy_bin = self.plugin_context.args.clang_tidy_bin

        flags: List[str] = [
            "-header-filter=" + package["src_dir"] + "/.*",
            "-p",
            package["bin_dir"] + "/compile_commands.json",
            "-extra-arg=-fopenmp=libomp",
        ]
        flags += self.get_user_flags(level)

        files: List[str] = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]

        try:
            output = subprocess.check_output(
                [clang_tidy_bin] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            if (
                "clang-diagnostic-error" in output
            ):  # pylint: disable=unsupported-membership-test
                raise subprocess.CalledProcessError(-1, clang_tidy_bin, output)
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("clang-tidy failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", clang_tidy_bin, ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                fid.write(output)

        issues: List[Issue] = self.parse_tool_output(output)
        return issues

    @classmethod
    def check_for_exceptions(cls, match: Match[str]) -> bool:
        """Manual exceptions."""
        # You are allowed to have 'using namespace' in source files
        if (
            match.group(1).endswith(".cpp") or match.group(1).endswith(".cc")
        ) and match.group(6) == "google-build-using-namespace":
            return True
        return False

    def parse_tool_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        clang_tidy_re = r"(.+):(\d+):(\d+):\s(.+):\s(.+)\s\[(.+)\]"
        parse: Pattern[str] = re.compile(clang_tidy_re)
        issues: List[Issue] = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match and not self.check_for_exceptions(match):
                if (
                    line[1] != "*"
                    and match.group(3) != "information"
                    and match.group(4) != "note"
                ):
                    cert_reference = None
                    if match.group(6) in warnings_mapping:
                        cert_reference = warnings_mapping[match.group(6)]
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            match.group(4) + "/" + match.group(6),
                            "3",
                            match.group(5),
                            cert_reference,
                        )
                    )
        return issues
