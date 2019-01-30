"""Tool plugin."""

from __future__ import print_function

import shlex

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
