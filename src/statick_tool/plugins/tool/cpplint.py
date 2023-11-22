"""Apply Cpplint tool and gather results."""
import logging
import os
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CpplintToolPlugin(ToolPlugin):
    """Apply Cpplint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "cpplint"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "make_targets" not in package and "headers" not in package:
            return []

        if not package["make_targets"] and not package["headers"]:
            return []

        if "cpplint" not in package:
            logging.warning("  cpplint not found!")
            return None

        flags: List[str] = []
        flags += self.get_user_flags(level)
        cpplint = package["cpplint"]

        files: List[str] = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]

        try:
            output = subprocess.check_output(
                [cpplint] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("cpplint failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find cpplint executable! (%s)", ex)
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
        if (
            match.group(1).endswith(".cpp") or match.group(1).endswith(".cc")
        ) and match.group(4) == "build/namespaces":
            # allow using namespace inside source files
            return True
        if match.group(4) == "build/namespaces" and "unnamed" in match.group(3):
            # ignore anonymous namespace warning
            return True
        if (
            "cfg/cpp" in match.group(1)
            and match.group(1).endswith("Config.h")
            and match.group(4) == "build/storage_class"
        ):
            # ignoring issue in auto-generated ROS code
            return True
        return False

    def parse_tool_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        lint_re = r"(.+):(\d+):\s(.+)\s\[(.+)\]\s\[(\d+)\]"
        parse: Pattern[str] = re.compile(lint_re)
        issues: List[Issue] = []
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match and not self.check_for_exceptions(match):
                norm_path = os.path.normpath(match.group(1))
                issues.append(
                    Issue(
                        norm_path,
                        match.group(2),
                        self.get_name(),
                        match.group(4),
                        match.group(5),
                        match.group(3),
                        None,
                    )
                )
        return issues
