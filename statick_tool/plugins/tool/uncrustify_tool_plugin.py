"""Apply uncrustify tool and gather results."""

from __future__ import print_function

import difflib
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class UncrustifyToolPlugin(ToolPlugin):
    """Apply uncrustify tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "uncrustify"

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("--uncrustify-bin", dest="uncrustify_bin",
                          type=str, help="uncrustify binary path")

    def scan(self, package, level):  # pylint: disable=too-many-locals, too-many-branches
        """Run tool and gather output."""
        if "make_targets" not in package and "headers" not in package:
            return []

        uncrustify_bin = "uncrustify"
        if self.plugin_context.args.uncrustify_bin is not None:
            uncrustify_bin = self.plugin_context.args.uncrustify_bin

        flags = []
        flags += self.get_user_flags(level)

        files = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
        if "headers" in package:
            files += package["headers"]

        total_output = []

        try:
            format_file_name = self.plugin_context.resources.get_file("uncrustify.cfg")

            for src in files:
                format_file_name = self.plugin_context.resources.get_file("uncrustify.cfg")
                cmd = [uncrustify_bin, '-c', format_file_name, '-f', src]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                                 universal_newlines=True)
                src_cmd = ['cat', src]
                src_output = subprocess.check_output(src_cmd, stderr=subprocess.STDOUT,
                                                     universal_newlines=True)
                diff = difflib.context_diff(output.splitlines(), src_output.splitlines())
                found_diff = False
                output = output.split('\n', 1)[1]
                for line in diff:
                    if line.startswith('---') or line.startswith('***') \
                            or line.startswith('! Parsing') or src in line \
                            or line.isspace():
                        continue
                    # This is a bug I can't figure out yet.
                    if '#ifndef' in line or '#define' in line:
                        continue
                    found_diff = True
                if found_diff:
                    total_output.append(src)

        except subprocess.CalledProcessError as ex:
            output = ex.output
            print("uncrustify failed! Returncode = {}".format(str(ex.returncode)))
            print("{}".format(ex.output))
            return None

        except OSError as ex:
            print("Couldn't find uncrustify executable! ({})".format(ex))
            return None

        if self.plugin_context.args.show_tool_output:
            for output in total_output:
                print("{}".format(output))

        with open(self.get_name() + ".log", "w") as fname:
            for output in total_output:
                fname.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output):
        """Parse tool output and report issues."""
        issues = []
        for output in total_output:
            issues.append(Issue(output, "0", self.get_name(), "format",
                                "1", "Uncrustify mis-match", None))

        return issues
