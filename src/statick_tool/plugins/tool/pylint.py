"""Apply pylint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PylintToolPlugin(ToolPlugin):
    """Apply pylint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "pylint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    def get_binary(  # pylint: disable=unused-argument
        self, level: Optional[str] = None, package: Optional[Package] = None
    ) -> str:
        """Get tool binary name."""
        return self.get_name()

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output."""
        flags: list[str] = [
            "--msg-template='{abspath}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
            "--reports=no",
        ]
        flags += user_flags
        if self.plugin_context and self.plugin_context.args.max_procs is not None:
            flags += [f"-j {self.plugin_context.args.max_procs}"]

        tool_bin = self.get_binary()

        total_output: list[str] = []

        try:
            subproc_args = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            if ex.returncode != 32:
                output = ex.output
            else:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find pylint executable! (%s)", ex)
            return None

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""
        pylint_re = r"(.+):(\d+):\s\[(.+)\]\s(.+)"
        parse: Pattern[str] = re.compile(pylint_re)
        issues: list[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    if "," in match.group(3):
                        parts = match.group(3).split(",")
                        if parts[1].strip() == "":
                            issues.append(
                                Issue(
                                    match.group(1),
                                    int(match.group(2)),
                                    self.get_name(),
                                    parts[0],
                                    5,
                                    match.group(4),
                                    None,
                                )
                            )
                        else:
                            issues.append(
                                Issue(
                                    match.group(1),
                                    int(match.group(2)),
                                    self.get_name(),
                                    parts[0],
                                    5,
                                    parts[1].strip() + ": " + match.group(4),
                                    None,
                                )
                            )
                    else:
                        issues.append(
                            Issue(
                                match.group(1),
                                int(match.group(2)),
                                self.get_name(),
                                match.group(3),
                                5,
                                match.group(4),
                                None,
                            )
                        )

        return issues
