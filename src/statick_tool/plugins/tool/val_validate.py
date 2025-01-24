"""Apply VAL Validate tool and gather results.

Tool is from King's College London. Tool authors are:

- Maria Fox and Derek Long - PDDL2.2 and VAL
- Richard Howey - PDDL2.2 and VAL and Continuous Effects, derived predicates,
  timed initial literals and LaTeX report in VAL
- Stephen Cresswell - PDDL2.2 Parser

https://github.com/KCL-Planning/VAL/tree/master/applications#validate
"""
import argparse
import logging
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ValValidateToolPlugin(ToolPlugin):  # type: ignore
    """Apply Validate tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "val_validate"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--val-validate-bin",
            dest="val_validate_bin",
            type=str,
            help="VAL Validate binary path",
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "pddl_domain_src" not in package or not package["pddl_domain_src"]:
            return []

        flags: List[str] = ["-v"]
        flags += self.get_user_flags(level)

        validate_bin = "Validate"
        if self.plugin_context.args.val_validate_bin is not None:
            validate_bin = self.plugin_context.args.val_validate_bin

        try:
            subproc_args: List[str] = (
                [validate_bin]
                + flags
                + package["pddl_domain_src"]
                + package["pddl_problem_src"]
            )
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 255:
                logging.warning("VAL Validate failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", validate_bin, ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf-8") as fid:
                fid.write(output)

        issues: List[Issue] = self.parse_tool_output(
            output, package["pddl_domain_src"][0]
        )
        return issues

    def parse_tool_output(self, output: str, filename: str) -> List[Issue]:
        """Parse tool output and report issues."""
        issues: List[Issue] = []
        issue_found = False
        for item in output.splitlines():
            if item.startswith("Error:"):
                issue_found = True
                warning_level = "3"
                line_number = "0"
                issue_type = "0"
                msg = "Exact file and line number unknown. " + item.lstrip("Error: ")

            if item.startswith("Problem"):
                issue_found = True
                warning_level = "3"
                line_number = "0"
                issue_type = "1"
                msg = "Exact file and line number unknown. " + item

            if issue_found:
                issue = Issue(
                    filename,
                    line_number,
                    self.get_name(),
                    issue_type,
                    warning_level,
                    msg,
                    None,
                )

                issues.append(issue)

        return issues
