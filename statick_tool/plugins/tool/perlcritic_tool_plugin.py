"""Apply Perl::Critic tool and gather results."""

from __future__ import print_function
import csv
import os
import subprocess
import shlex

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


class PerlCriticToolPlugin(ToolPlugin):
    """Apply Perl::Critic tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "perlcritic"

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("--perlcritic-bin", dest="perlcritic_bin", type=str,
                          help="perlcritic binary path")

    def scan(self, package, level):
        """Run tool and gather output."""
        if "perl_src" not in package:
            return []
        elif len(package["perl_src"]) == 0:
            return []

        perlcritic_bin = "perlcritic"
        if self.plugin_context.args.perlcritic_bin is not None:
            perlcritic_bin = self.plugin_context.args.perlcritic_bin

        flags = ["--nocolor", "--verbose=%f:::%l:::%p:::%m:::%s\n"]
        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = flags + list(lex)

        files = []
        if "perl_src" in package:
            files += package["perl_src"]

        try:
            output = subprocess.check_output([perlcritic_bin] + flags + files,
                                             stderr=subprocess.STDOUT).join(' ')

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 2:
                print("perlcritic failed! Returncode = {}".
                      format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find %s! (%s)" % (perl_bin, ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output()
        return issues

    def parse_output(self):
        """Parse tool output and report issues."""
        issues = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        try:
            with open(self.get_name() + '.log', 'r') as logfile:
                for line in logfile:
                    split_line = line.replace(os.linesep, '').split(':::')

                    cert_reference = None
                    if split_line[2].replace('::', '__') in warnings_mapping.keys():
                        cert_reference = warnings_mapping[split_line[2].replace('::', '__')]

                    print(split_line)
                    issues.append(Issue(split_line[0], split_line[1].replace(os.linesep, ' '),
                                        self.get_name(), split_line[2],
                                        split_line[3], split_line[2], cert_reference))
        except IOError:
            # We couldn't find the results file for some reason
            pass

        return issues
