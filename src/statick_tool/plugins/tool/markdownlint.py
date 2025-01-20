"""Apply markdownlint tool and gather results."""

import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class MarkdownlintToolPlugin(ToolPlugin):  # type: ignore
    """Apply markdownlint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "markdownlint"

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["md_src"]

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        tool_bin = "markdownlint"

        tool_config = ".markdownlintrc"
        user_config = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "config"
        )
        if user_config is not None:
            tool_config = user_config

        format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: List[str] = []
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += user_flags

        total_output: List[str] = []

        try:
            exe = [tool_bin] + flags + files
            output = subprocess.check_output(
                exe, stderr=subprocess.STDOUT, universal_newlines=True
            )
            total_output.append(output)

        except subprocess.CalledProcessError as ex:
            if (
                "Error: Cannot find module" in ex.output
                or "Require stack:" in ex.output
            ):
                # nodejs cannot find a module and threw an error
                # this results in the same returncode `1` that markdownlint
                # uses to indicate the presence of linting issues.
                logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None
            if ex.returncode == 1:  # markdownlint returns 1 upon linting errors
                total_output.append(ex.output)
            else:
                logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    # pylint: enable=too-many-locals

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        markdownlint_re = r"(.+):(\d+)\s([^\s]+)\s(.+)"
        markdownlint_re_with_col = r"(.+):(\d+):(\d+)\s([^\s]+)\s(.+)"
        parse: Pattern[str] = re.compile(markdownlint_re)
        parse_with_col: Pattern[str] = re.compile(markdownlint_re_with_col)
        issues: List[Issue] = []

        for output in total_output:
            for line in output.split("\n"):
                match_with_col: Optional[Match[str]] = parse_with_col.match(line)
                if match_with_col:
                    issues.append(
                        Issue(
                            match_with_col.group(1),
                            match_with_col.group(2),
                            self.get_name(),
                            match_with_col.group(4),
                            3,
                            match_with_col.group(5),
                            None,
                        )
                    )
                else:
                    match: Optional[Match[str]] = parse.match(line)
                    if match:
                        issues.append(
                            Issue(
                                match.group(1),
                                match.group(2),
                                self.get_name(),
                                match.group(3),
                                3,
                                match.group(4),
                                None,
                            )
                        )
        return issues
