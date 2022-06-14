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

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""
        return ["python_src"]

    def process_files(
        self, package: Package, level: str, files: List[str], user_flags: List[str]
    ) -> Optional[List[str]]:
        """Run tool and gather output."""
        bandit_bin: str = "bandit"
        if self.plugin_context and self.plugin_context.args.bandit_bin is not None:
            bandit_bin = self.plugin_context.args.bandit_bin

        flags: List[str] = ["--format=csv"]
        flags += user_flags

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
        return output.splitlines()

    def parse_output(
        self, total_output: List[str], package: Optional[Package] = None
    ) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []

        # Copy output for modification
        output_minus_log = list(total_output)

        # Bandit prints a bunch of log messages out and you can't suppress
        # them, so iterate over the list until we find the CSV header
        for line in total_output:  # Intentionally total_output, not output_minus_log
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
