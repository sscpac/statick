"""Apply Cpplint tool and gather results."""

from __future__ import print_function
import subprocess
import shlex
import re
import os

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


class CpplintToolPlugin(ToolPlugin):
    """Apply Cpplint tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "cpplint"

    def get_tool_dependencies(self):
        """Get a list of tools that must run before this one."""
        return ["make"]

    def scan(self, package, level):
        """Run tool and gather output."""
        if "cpplint" not in package:
            print("  cpplint not found!")
            return []

        if "make_targets" not in package and "headers" not in package:
            return []

        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = list(lex)

        cpplint = package["cpplint"]

        files = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]

        try:
            output = subprocess.check_output([cpplint] + flags + files,
                                             stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("cpplint failed! Returncode = {}".
                      format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find cpplint executable! (%s)" % (ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output(output)
        return issues

    @classmethod
    def check_for_exceptions(cls, match):
        """Manual exceptions."""
        if (match.group(1).endswith(".cpp") or
                match.group(1).endswith(".cc")) and \
                match.group(4) == "build/namespaces":
            # allow using namespace inside source files
            return True
        elif match.group(4) == "build/namespaces" and \
                "unnamed" in match.group(3):
            # ignore anonymous namespace warning
            return True
        elif "cfg/cpp" in match.group(1) and \
                match.group(1).endswith("Config.h") and \
                match.group(4) == "build/storage_class":
            # ignoring issue in auto-generated ROS code
            return True
        else:
            return False

    def parse_output(self, output):
        """Parse tool output and report issues."""
        lint_re = r"(.+):(\d+):\s(.+)\s\[(.+)\]\s\[(\d+)\]"
        parse = re.compile(lint_re)
        issues = []
        for line in output.split('\n'):
            match = parse.match(line)
            if match and not self.check_for_exceptions(match):
                norm_path = os.path.normpath(match.group(1))
                issues.append(Issue(norm_path, match.group(2), self.get_name(),
                                    match.group(4), match.group(5),
                                    match.group(3), None))
        return issues
