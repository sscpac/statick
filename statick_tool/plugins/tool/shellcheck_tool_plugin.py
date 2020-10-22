"""
Apply shellcheck tool and gather results.

The output from the tool is collected in JSON format to facilitate parsing.
"""
import argparse
import json
import subprocess
from typing import Any, List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ShellcheckToolPlugin(ToolPlugin):
    """Apply shellcheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "shellcheck"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--shellcheck-bin",
            dest="shellcheck_bin",
            type=str,
            help="shellcheck binary path",
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "shell_src" not in package or not package["shell_src"]:
            return []

        shellcheck_bin = "shellcheck"  # type: str
        if self.plugin_context and self.plugin_context.args.shellcheck_bin is not None:
            shellcheck_bin = self.plugin_context.args.shellcheck_bin

        # Get output in GCC format.
        flags = ["-f", "json"]  # type: List[str]
        flags += self.get_user_flags(level)

        files = []  # type: List[str]
        if "shell_src" in package:
            files += package["shell_src"]

        try:
            subproc_args = [shellcheck_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        # We expect a CalledProcessError if issues are discovered by the tool.
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("shellcheck failed! Returncode = {}".format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find {}! ({})".format(shellcheck_bin, ex))
            return None

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as f:
                f.write(output)

        issues = self.parse_output(json.loads(output))
        return issues

    def parse_output(self, output: Any) -> List[Issue]:
        """Parse tool output and report issues."""
        issues = []  # type: List[Issue]
        for item in output:
            if (
                "level" not in item
                or "file" not in item
                or "line" not in item
                or "code" not in item
                or "message" not in item
            ):
                if self.plugin_context and self.plugin_context.args.show_tool_output:
                    print("  Found invalid shellcheck output: {}".format(item))
                continue
            if item["level"] == "style":
                warning_level = "1"
            elif item["level"] == "info":
                warning_level = "1"
            elif item["level"] == "warning":
                warning_level = "3"
            elif item["level"] == "error":
                warning_level = "5"
            else:
                warning_level = "3"

            issue = Issue(
                item["file"],
                str(item["line"]),
                self.get_name(),
                "SC" + str(item["code"]),
                warning_level,
                item["message"],
                None,
            )

            issues.append(issue)

        return issues
