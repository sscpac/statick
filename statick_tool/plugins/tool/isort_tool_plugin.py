"""Apply isort tool and gather results.

The isort tool will only find if a file has issues with imports. To automatically fix
the issues you can run `isort <file>`.
"""
from typing import List

import isort

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
        flags: List[str] = ["--check-only"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output: List[str] = []

        for src in package["python_src"]:
            if not isort.check_file(src):  # type: ignore
                total_output.append(src)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
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
