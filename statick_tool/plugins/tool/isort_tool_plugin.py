"""Apply isort tool and gather results."""
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class IsortToolPlugin(ToolPlugin):
    """Apply isort tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "isort"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags = ["--check-only"]
        user_flags = self.get_user_flags(level)
        flags += user_flags

        total_output = []

        tool_bin = "isort"
        for src in package["python_src"]:
            try:
                subproc_args = [tool_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

            logging.debug("%s", output)

            total_output.append(output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                for output in total_output:
                    fid.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues = []

        for output in total_output:
            if not output or output.split()[0] != "ERROR:":
                continue
            filename = output.split()[1]
            msg = output.split(filename, 1)[1].lstrip(" ")
            issues.append(
                Issue(
                    filename,
                    "0",
                    self.get_name(),
                    "formatting",
                    "3",
                    msg,
                    None,
                )
            )

        return issues
