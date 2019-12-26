"""Apply clang-format tool and gather results."""

from __future__ import print_function

import difflib
import re
import subprocess

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class ClangFormatToolPlugin(ToolPlugin):
    """Apply clang-format tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "clang-format"

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("--clang-format-bin", dest="clang_format_bin",
                          type=str, help="clang-format binary path")
        args.add_argument("--clang-format-raise-exception",
                          dest="clang_format_raise_exception",
                          action="store_true",
                          help="clang-format raise exception on mismatched "
                               "configuration file")
        args.add_argument("--clang-format-ignore-exception",
                          dest="clang_format_raise_exception",
                          action="store_false",
                          help="clang-format ignore exception on mismatched "
                               "configuration file")
        args.set_defaults(clang_format_raise_exception=True)

    def scan(self, package, level):  # pylint: disable=too-many-locals, too-many-branches
        """Run tool and gather output."""
        if "make_targets" not in package and "headers" not in package:
            return []

        user_version = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                  level,
                                                                  "version")

        clang_format_bin = "clang-format"
        if user_version is not None:
            clang_format_bin = "{}-{}".format(clang_format_bin, user_version)

        # If the user explicitly specifies a binary, let that override the user_version
        if self.plugin_context.args.clang_format_bin is not None:
            clang_format_bin = self.plugin_context.args.clang_format_bin

        files = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
        if "headers" in package:
            files += package["headers"]

        total_output = []

        try:
            output = subprocess.check_output([clang_format_bin,
                                              "--dump-config"],
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            format_file_name = self.plugin_context.resources.get_file("_clang-format")
            with open(format_file_name, "r") as format_file:
                target_format = format_file.read()
            diff = difflib.context_diff(output.splitlines(),
                                        target_format.splitlines())
            for line in diff:
                if line.startswith("+ ") or line.startswith("- ") or \
                   line.startswith("! "):
                    if line[2:].strip() and line[2:].strip()[0] != "#":
                        # pylint: disable=line-too-long
                        exc = subprocess.CalledProcessError(-1,
                                                            clang_format_bin,
                                                            ".clang-format style is not correct. There is one located in {}. Put this file in your home directory.".
                                                            format(format_file_name))
                        # pylint: enable=line-too-long
                        if self.plugin_context.args.clang_format_raise_exception:
                            raise exc

            for src in files:
                output = subprocess.check_output([clang_format_bin, src,
                                                  "-output-replacements-xml"],
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)
                output = src + "\n" + output
                if self.plugin_context.args.clang_format_raise_exception:
                    total_output.append(output)

        except subprocess.CalledProcessError as ex:
            output = ex.output
            print("clang-format failed! Returncode = {}".format(str(ex.returncode)))
            print("{}".format(ex.output))
            if self.plugin_context.args.clang_format_raise_exception:
                return None
            return []

        except OSError as ex:
            print("Couldn't find {}! ({})".format(clang_format_bin, ex))
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
        clangformat_re = r"<replacement offset="
        parse = re.compile(clangformat_re)
        issues = []

        for output in total_output:
            lines = output.splitlines()
            filename = lines[0]
            count = 0
            for line in lines:
                match = parse.match(line)
                if match:
                    count += 1
            if count > 0:
                issues.append(Issue(filename, "0", self.get_name(), "format",
                                    "1", str(count) + " replacements", None))
        return issues
