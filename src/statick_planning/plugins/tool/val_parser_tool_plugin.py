"""Apply VAL Parser tool and gather results.

Tool is from King's College London. Tool authors are:

- Maria Fox and Derek Long - PDDL2.2 and VAL
- Richard Howey - PDDL2.2 and VAL and Continuous Effects, derived predicates,
  timed initial literals and LaTeX report in VAL
- Stephen Cresswell - PDDL2.2 Parser

https://github.com/KCL-Planning/VAL/tree/master/applications#parser
"""
import argparse
import logging
import re
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ValParserToolPlugin(ToolPlugin):  # type: ignore
    """Apply Parser tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "val_parser"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--val-parser-bin",
            dest="val_parser_bin",
            type=str,
            help="VAL Parser binary path",
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "pddl_domain_src" not in package or not package["pddl_domain_src"]:
            return []

        flags = []
        flags += self.get_user_flags(level)

        parser_bin = "Parser"
        if self.plugin_context.args.val_parser_bin is not None:
            parser_bin = self.plugin_context.args.val_parser_bin

        try:
            subproc_args = (
                [parser_bin]
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
                logging.warning("VAL Parser failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", parser_bin, ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf-8") as fid:
                fid.write(output)

        issues = self.parse_output(output)  # type: List[Issue]
        return issues

    def parse_output(self, output: str) -> List[Issue]:
        """Parse tool output and report issues."""
        tool_re = r"(.+):\s(.+):\s(.+):\s(.+):\s(.+)\s(.+)"  # type: str
        parse = re.compile(tool_re)  # type: Pattern[str]
        issues = []
        issue_found = False

        for line in output.splitlines():
            # If we find this pattern then all following lines will have an issue per
            # line. That's when we start parsing.
            if line.startswith("Errors:") and "warnings:" in line:
                issue_found = True
                continue

            if issue_found:
                match = parse.match(line)  # type: Optional[Match[str]]
                if match:
                    warning_level = "1"
                    if match.group(4) == "Warning":
                        warning_level = "3"
                    elif match.group(4) == "Error":
                        warning_level = "5"

                    issue = Issue(
                        match.group(1),
                        match.group(3),
                        self.get_name(),
                        "PDDL",
                        warning_level,
                        match.group(5) + " " + match.group(6),
                        None,
                    )

                    issues.append(issue)

        return issues
