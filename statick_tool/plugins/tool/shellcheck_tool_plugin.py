"""Apply shellcheck tool and gather results."""
import argparse
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ShellcheckToolPlugin(ToolPlugin):
    """Apply shellcheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "shellcheck"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--shellcheck-bin",
            dest="shellcheck_bin",
            type=str,
            help="shellcheck binary path",
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "shell_src" not in package or not package["shell_src"]:
            return []

        shellcheck_bin = "shellcheck"  # type: str
        if self.plugin_context and self.plugin_context.args.shellcheck_bin is not None:
            shellcheck_bin = self.plugin_context.args.shellcheck_bin

        flags = self.get_user_flags(level)  # type: List[str]

        files = []  # type: List[str]
        if "shell_src" in package:
            files += package["shell_src"]

        for src in files:
            try:
                subproc_args = [shellcheck_bin, src] + flags
                output = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
                )

            # We expect a CalledProcessError if issues are discovered by the tool.
            except subprocess.CalledProcessError as ex:
                output = ex.output
                if ex.returncode != 1:
                    print(
                        "shellcheck failed! Returncode = {}".format(str(ex.returncode))
                    )
                    print("{}".format(ex.output))
                    return None

            except OSError as ex:
                print("Couldn't find {}! ({})".format(shellcheck_bin, ex))
                return None

            if self.plugin_context and self.plugin_context.args.show_tool_output:
                print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w") as f:
                f.write(output)

        issues = self.parse_output(output.splitlines())
        return issues

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues = []
        found_file = False
        found_msg = False
        filename = ""
        line = ""
        msg = ""
        issue_type = ""

        for output in total_output:
            if output.lstrip().startswith("In "):
                filename = output.split(" ")[1]
                line = output.split(" ")[3].rstrip(":")
                found_file = True
            if output.lstrip().startswith("^"):
                msg = output.split(":")[1].lstrip().rstrip()
                if len(output.split(":")) > 2:
                    msg += ":" + output.split(":")[2].rstrip()
                issue_type = output.lstrip().split(" ")[1].rstrip(":")
                found_msg = True
            if found_file and found_msg:
                issues.append(
                    Issue(
                        filename,
                        line,
                        self.get_name(),
                        issue_type,
                        "3",
                        msg,
                        None,
                    )
                )
                found_file = False
                found_msg = False
                filename = ""
                line = ""
                msg = ""
                issue_type = ""

        return issues
