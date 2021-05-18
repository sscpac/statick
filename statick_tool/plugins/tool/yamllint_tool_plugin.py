"""Apply yamllint tool and gather results."""
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class YamllintToolPlugin(ToolPlugin):
    """Apply yamllint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "yamllint"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        flags: List[str] = ["-f", "parsable"]
        flags += self.get_user_flags(level)

        total_output: List[str] = []

        for yaml_file in package["yaml"]:
            try:
                subproc_args = ["yamllint", yaml_file] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:
                    output = ex.output
                else:
                    logging.warning("Problem %d", ex.returncode)
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find yamllint executable! (%s)", ex)
                return None

            logging.debug("%s: %s", yaml_file, output)

            total_output.append(output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                for output in total_output:
                    fid.write(output)

        issues: List[Issue] = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        yamllint_re = r"(.+):(\d+):(\d+):\s\[(.+)\]\s(.+)\s\((.+)\)"
        parse: Pattern[str] = re.compile(yamllint_re)
        issues: List[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issue_type = match.group(4)
                    if issue_type == "error":
                        level = "5"
                    else:
                        level = "3"
                    issues.append(
                        Issue(
                            match.group(1),
                            match.group(2),
                            self.get_name(),
                            match.group(6),
                            level,
                            match.group(5),
                            None,
                        )
                    )

        return issues
