"""Apply bandit tool and gather results."""
import argparse
import csv
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class BanditToolPlugin(ToolPlugin):
    """Apply bandit tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "bandit"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--bandit-bin", dest="bandit_bin", type=str, help="bandit binary path"
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "python_src" not in package:
            return []
        if not package["python_src"]:
            return []

        bandit_bin: str = "bandit"
        if self.plugin_context and self.plugin_context.args.bandit_bin is not None:
            bandit_bin = self.plugin_context.args.bandit_bin

        flags: List[str] = ["--format=csv"]
        flags += self.get_user_flags(level)

        files: List[str] = []
        if "python_src" in package:
            files += package["python_src"]

        try:
            output = subprocess.check_output(
                [bandit_bin] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("bandit failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", bandit_bin, ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fid:
                fid.write(output)

        issues: List[Issue] = self.parse_output(output.splitlines())
        return issues

    def parse_output(self, output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        # Copy output for modification
        output_minus_log = list(output)

        # Bandit prints a bunch of log messages out and you can't suppress
        # them, so iterate over the list until we find the CSV header
        for line in output:  # Intentionally output, not output_minus_log
            if line.startswith("filename"):
                # Found the CSV header, stop removing things
                break
            output_minus_log.remove(line)

        csvreader = csv.DictReader(output_minus_log)
        for csv_line in csvreader:
            severity = "1"
            if csv_line["issue_confidence"] == "MEDIUM":
                severity = "3"
            elif csv_line["issue_confidence"] == "HIGH":
                severity = "5"
            issues.append(
                Issue(
                    csv_line["filename"],
                    csv_line["line_number"],
                    self.get_name(),
                    csv_line["test_id"],
                    severity,
                    csv_line["issue_text"],
                    None,
                )
            )

        return issues
