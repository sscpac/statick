"""Apply rst-lint tool and gather results."""

import logging
from typing import List, Optional

import restructuredtext_lint
from docutils.utils import SystemMessage

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class RstlintToolPlugin(ToolPlugin):  # type: ignore
    """Apply rst-lint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "rstlint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags: List[str] = []
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: List[str] = []
        if "rst_src" in package:
            files += package["rst_src"]

        total_output: List[SystemMessage] = []

        for src in files:
            output = restructuredtext_lint.lint_file(src, None, flags)
            total_output.extend(output)

        for output in total_output:
            logging.debug("%s", str(output))

        with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
            for output in total_output:
                fid.write(str(output))

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    # pylint: enable=too-many-locals

    def parse_output(self, total_output: List[SystemMessage]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        for output in total_output:
            issues.append(
                Issue(
                    output.source,
                    output.line,
                    self.get_name(),
                    output.type,
                    output.level,
                    output.message,
                    None,
                )
            )
        return issues
