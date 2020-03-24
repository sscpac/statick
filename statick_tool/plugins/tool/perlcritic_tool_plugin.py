"""Apply Perl::Critic tool and gather results."""
import argparse
import subprocess
from typing import List, Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PerlCriticToolPlugin(ToolPlugin):
    """Apply Perl::Critic tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool."""
        return "perlcritic"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""
        args.add_argument(
            "--perlcritic-bin",
            dest="perlcritic_bin",
            type=str,
            help="perlcritic binary path",
        )

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        if "perl_src" not in package:
            return []
        if not package["perl_src"]:
            return []

        perlcritic_bin = "perlcritic"
        if self.plugin_context and self.plugin_context.args.perlcritic_bin is not None:
            perlcritic_bin = self.plugin_context.args.perlcritic_bin

        flags = ["--nocolor", "--verbose=%f:::%l:::%p:::%m:::%s\n"]
        flags += self.get_user_flags(level)

        files = []  # type: List[str]
        if "perl_src" in package:
            files += package["perl_src"]

        try:
            output = subprocess.check_output(
                [perlcritic_bin] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            ).join(" ")

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 2:
                print("perlcritic failed! Returncode = {}".format(str(ex.returncode)))
                print("{}".format(ex.output))
                return []

        except OSError as ex:
            print("Couldn't find {}! ({})".format(perlcritic_bin, ex))
            return []

        if self.plugin_context and self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "wt") as f:
                f.write(output)

        issues = self.parse_output(output.splitlines())

        return issues

    def parse_output(self, output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""
        issues = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in output:
            split_line = line.strip().split(":::")
            # Should split into five segments, anything less is invalid.
            if len(split_line) < 5:
                continue
            cert_reference = None
            if split_line[2].replace("::", "__") in warnings_mapping.keys():
                cert_reference = warnings_mapping[split_line[2].replace("::", "__")]

            issues.append(
                Issue(
                    split_line[0],
                    split_line[1],
                    self.get_name(),
                    split_line[2],
                    split_line[4],
                    split_line[3],
                    cert_reference,
                )
            )

        return issues
