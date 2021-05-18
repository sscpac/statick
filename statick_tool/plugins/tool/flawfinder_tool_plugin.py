"""Apply flawfinder tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class FlawfinderToolPlugin(ToolPlugin):
    """Apply flawfinder tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "flawfinder"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "c_src" not in package:
            return []

        flags: List[str] = ["--quiet", "-D", "--singleline"]
        flags += self.get_user_flags(level)
        total_output: List[str] = []

        for src in package["c_src"]:
            try:
                subproc_args = ["flawfinder"] + flags + [src]
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )
            except subprocess.CalledProcessError as ex:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

            except OSError as ex:
                logging.warning("Couldn't find flawfinder executable! (%s)", ex)
                return None

            logging.debug("%s", output)

            total_output.append(output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                for output in total_output:
                    fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        flawfinder_re = r"(.+):(\d+):\s+\[(\d+)\]\s+(.+):\s*(.+)"
        parse: Pattern[str] = re.compile(flawfinder_re)
        issues: List[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            match.group(4),
                            match.group(3),
                            match.group(5),
                            None,
                        )
                    )

        return issues
