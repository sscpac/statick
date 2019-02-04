"""Tool plugin."""

from __future__ import print_function

import os
import shlex
import sys

from yapsy.IPlugin import IPlugin


class ToolPlugin(IPlugin):
    """Default implementation of tool plugin."""

    plugin_context = None

    def get_name(self):
        """Get name of tool."""
        pass

    @classmethod
    def get_tool_dependencies(cls):
        """Get a list of tools that must run before this one."""
        return []

    def gather_args(self, args):
        """Gather arguments."""
        pass

    def scan(self, package, level):
        """Run tool and gather output."""
        pass

    def set_plugin_context(self, plugin_context):
        """Set the plugin context."""
        self.plugin_context = plugin_context

    def load_mapping(self):
        """Load a mapping between warnings and identifiers."""
        file_name = "plugin_mapping/%s.txt" % (self.get_name())
        full_path = self.plugin_context.resources.get_file(file_name)
        if full_path is None:
            return {}
        warning_mapping = {}
        with open(full_path, 'r') as mapping_file:
            for line in mapping_file.readlines():
                split_line = line.strip().split(':')
                if len(split_line) != 2:
                    print("Warning: invalid line %s in file %s" %
                          (line, file_name))
                    continue
                warning_mapping[split_line[0]] = split_line[1]
        return warning_mapping

    def get_user_flags(self, level, name=None):
        """Get the user-defined extra flags for a specific tool/level combination."""
        if name is None:
            name = self.get_name()
        user_flags = self.plugin_context.config.get_tool_config(name, level,
                                                                "flags")
        flags = []
        if user_flags:
            lex = shlex.shlex(user_flags, posix=True)
            lex.whitespace_split = True
            flags = list(lex)
        return flags

    @staticmethod
    def is_valid_executable(path):
        """Return whether a provided command exists and is executable."""
        return os.path.isfile(path) and os.access(path, os.X_OK)

    @staticmethod
    def command_exists(command):
        """Return whether a particular command is available on $PATH"""

        if sys.platform == 'win32':
            # Tack .exe on if the command doesn't have an extension
            _, extension = os.path.splitext(command)
            if not extension:
                command += '.exe'

        fpath, fname = os.path.split(command)

        if fpath:
            # Contains a path, not just a command, so don't search PATH
            return ToolPlugin.is_valid_executable(command)

        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_path = os.path.join(path, command)
                if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                    return True

        return False
