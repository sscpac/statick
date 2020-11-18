"""Apply VAL tool and gather results."""
import argparse
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ValToolPlugin(ToolPlugin):  # type: ignore
    """Apply VAL tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "val"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument("--val-bin", dest="val_bin", type=str, help="VAL binary path")

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "pddl_domain_src" not in package or not package["pddl_domain_src"]:
            return []

        flags = ["-v"]
        flags += self.get_user_flags(level)

        val_bin = "Validate"
        if self.plugin_context.args.val_bin is not None:
            val_bin = self.plugin_context.args.val_bin

        try:
            subproc_args = (
                [val_bin]
                + flags
                + package["pddl_domain_src"]
                + package["pddl_problem_src"]
            )  # type: List[str]
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 255:
                print("VAL failed! Returncode = {}".format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find {}! ({})".format(val_bin, ex))
            return None

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as fname:
                fname.write(output)

        issues = self.parse_output(
            output, package["pddl_domain_src"][0]
        )  # type: List[Issue]
        return issues

    def parse_output(self, output: str, filename: str) -> List[Issue]:
        """Parse tool output and report issues."""
        issues = []
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
