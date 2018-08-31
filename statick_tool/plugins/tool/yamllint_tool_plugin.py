"""Apply yamllint tool and gather results."""

from __future__ import print_function
import subprocess
import shlex
import re

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


class YamllintToolPlugin(ToolPlugin):
    """Apply yamllint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "yamllint"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = ["-f", "parsable"]
        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = flags + list(lex)

        total_output = []

        for yaml_file in package["yaml"]:
            try:
                subproc_args = ["yamllint", yaml_file] + flags
                output = subprocess.check_output(subproc_args,
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:
                    output = ex.output
                else:
                    print("Problem {}".format(ex.returncode))
                    print("{}".format(ex.output))
                    return None
            except OSError as ex:
                print("Couldn't find yamllint executable! (%s)" % (ex))
                return None

            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))

            total_output.append(output)

        with open(self.get_name() + ".log", "w") as f:
            for output in total_output:
                f.write(output)

        issues = self.parse_output(total_output)
        return issues

    def parse_output(self, total_output):
        """Parse tool output and report issues."""
        yamllint_re = r"(.+):(\d+):(\d+):\s\[(.+)\]\s(.+)\s\((.+)\)"
        parse = re.compile(yamllint_re)
        issues = []

        for output in total_output:
            for line in output.split("\n"):
                match = parse.match(line)
                if match:
                    issue_type = match.group(4)
                    if issue_type == "error":
                        level = "5"
                    else:
                        level = "3"
                    issues.append(Issue(match.group(1), match.group(2),
                                        self.get_name(), match.group(6), level,
                                        match.group(5), None))

        return issues
