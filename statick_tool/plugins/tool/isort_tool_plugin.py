"""Apply isort tool and gather results.

The isort tool will only find if a file has issues with imports. To automatically fix
the issues you can run `isort <file>`.
"""
import logging
import subprocess
from typing import List

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class IsortToolPlugin(ToolPlugin):
    """Apply isort tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "isort"

    def scan(self, package: Package, level: str) -> List[Issue]:
        """Run tool and gather output."""
        tool_bin = "isort"
        flags: List[str] = ["--check-only"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output: List[str] = []

        for src in package["python_src"]:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except (IOError, OSError) as ex:
                logging.warning("isort binary failed: %s", tool_bin)
                logging.warning("Error = %s", ex.strerror)
                return []

            except subprocess.CalledProcessError as ex:
                logging.warning("isort binary failed: %s.", tool_bin)
                logging.warning("Returncode: %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                total_output.append(ex.output)
                continue

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                for output in total_output:
                    fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        for output in total_output:
            msg = "Imports are incorrectly sorted and/or formatted."
            issues.append(
                Issue(
                    output,
                    "0",
                    self.get_name(),
                    "formatting",
                    "3",
                    msg,
                    None,
                )
            )

        return issues
