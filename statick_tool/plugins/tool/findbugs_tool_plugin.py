"""Apply findbugs tool and gather results."""

from __future__ import print_function

import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class FindbugsToolPlugin(ToolPlugin):
    """Apply findbugs tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "findbugs"

    def get_tool_dependencies(self):
        """Get a list of tools that must run before this one."""
        return ["make"]

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("--findbugs-bin", dest="findbugs_bin", type=str,
                          help="findbugs binary path")

    def scan(self, package, level):
        """Run tool and gather output."""
        if "java_bin" not in package or not package["java_bin"]:
            return []

        findbugs_bin = "findbugs"
        if self.plugin_context.args.findbugs_bin is not None:
            findbugs_bin = self.plugin_context.args.findbugs_bin

        flags = ["-textui", "-effort:max", "-dontCombineWarnings",
                 "-longBugCodes", "-low"]
        flags += self.get_user_flags(level)

        include_file = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                  level, "include")
        exclude_file = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                  level, "exclude")
        if include_file is not None:
            flags += ["-include", self.plugin_context.resources.get_file(include_file)]

        if exclude_file is not None:
            flags += ["-exclude", self.plugin_context.resources.get_file(exclude_file)]

        files = []
        if "java_bin" in package:
            files += package["java_bin"]

        try:
            output = subprocess.check_output([findbugs_bin] + flags + files,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("findbugs failed! Returncode = {}".
                      format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find %s! (%s)" % (findbugs_bin, ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output(output)
        return issues

    def parse_output(self, output):
        """Parse tool output and report issues."""
        findbugs_re = r"\w \w (.+) \w+:\s+(.+)\s+(.+):\[line\s+(\d+)\]"
        parse = re.compile(findbugs_re)
        issues = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in output.split('\n'):
            match = parse.match(line)
            if match:
                cert_reference = None
                if match.group(1) in warnings_mapping:
                    cert_reference = warnings_mapping[match.group(1)]
                issues.append(Issue(match.group(3), match.group(4),
                                    self.get_name(), match.group(1),
                                    "3", match.group(2), cert_reference))
        return issues
