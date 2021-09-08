"""Apply proselint tool and gather results.

Website: http://proselint.com/
Github: https://github.com/amperser/proselint

The tool uses the default proselint configuration file.
On Ubuntu this is at `~/.config/proselint/config`.

https://github.com/amperser/proselint#checks
"""
import json
import logging
from typing import Any, Dict, List, Optional

import proselint
from proselint.config import default as proselint_default

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ProselintToolPlugin(ToolPlugin):  # type: ignore
    """Apply proselint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "proselint"

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "md_src" not in package or not package["md_src"]:
            return []

        files: List[str] = []
        if "md_src" in package:
            files += package["md_src"]

        # The JSON output does not include the filename so we have to run each file
        # one at a time, and store the output along with the filename in a dictionary.
        # The filename may be added to JSON output in the future:
        # https://github.com/amperser/proselint/issues/355
        output: Dict[str, Any] = {}
        for filename in files:
            with open(filename, encoding="utf8") as fid:
                errors = proselint.tools.errors_to_json(
                    proselint.tools.lint(fid, config=proselint_default)
                )
                output[filename] = errors

        for key, value in output.items():
            logging.debug("%s: %s", key, value)

        with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
            for key, value in output.items():
                combined = key + value
                fid.write(combined)

        issues: List[Issue] = self.parse_output(output)
        return issues

    def parse_output(self, output: Dict[str, Any]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []
        for key, value in output.items():
            try:
                data = json.loads(value)["data"]["errors"]
            except KeyError as ex:
                logging.warning("%s exception: %s", self.get_name(), ex)
                continue
            for item in data:
                if (
                    "check" not in item
                    or "line" not in item
                    or "message" not in item
                    or "severity" not in item
                ):
                    logging.debug("  Found invalid proselint output: %s", item)
                    continue
                if item["severity"] == "suggestion":
                    warning_level = "1"
                elif item["severity"] == "warning":
                    warning_level = "3"
                elif item["severity"] == "error":
                    warning_level = "5"
                else:
                    warning_level = "3"

                issue = Issue(
                    key,
                    str(item["line"]),
                    self.get_name(),
                    item["check"],
                    warning_level,
                    item["message"],
                    None,
                )

                issues.append(issue)

        return issues
