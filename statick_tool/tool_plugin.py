"""Tool plugin."""
import argparse
import os
import shlex
from typing import Any, Dict, List, Optional, Union

from yapsy.IPlugin import IPlugin

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class ToolPlugin(IPlugin):
    """Default implementation of tool plugin."""

    plugin_context = None

    def get_name(self) -> str:
        """Get name of tool."""
        pass  # pylint: disable=unnecessary-pass

    @classmethod
    def get_tool_dependencies(cls) -> List[str]:
        """Get a list of tools that must run before this one."""
        return []

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Set the plugin context."""
        self.plugin_context = plugin_context

    def load_mapping(self) -> Dict[str, str]:
        """Load a mapping between warnings and identifiers."""
        file_name = "plugin_mapping/{}.txt".format(self.get_name())  # type: str
        assert self.plugin_context is not None
        full_path = self.plugin_context.resources.get_file(
            file_name
        )  # type: Union[Any, str, None]
        if self.plugin_context.args.mapping_file_suffix is not None:
            # If the user specified a suffix, try to get the suffixed version of the file
            suffixed_file_name = "plugin_mapping/{}-{}.txt".format(
                self.get_name(), self.plugin_context.args.mapping_file_suffix
            )
            suffixed_full_path = self.plugin_context.resources.get_file(
                suffixed_file_name
            )
            if suffixed_full_path is not None:
                # If there actually is a file with that suffix, use it.
                # Else use the un-suffixed version.
                full_path = suffixed_full_path

        if full_path is None:
            return {}
        warning_mapping = {}  # type: Dict[str, str]
        with open(full_path, "r") as mapping_file:
            for line in mapping_file.readlines():
                split_line = line.strip().split(":")
                if len(split_line) != 2:
                    print("Warning: invalid line {} in file {}".format(line, file_name))
                    continue
                warning_mapping[split_line[0]] = split_line[1]
        return warning_mapping

    def get_user_flags(self, level: str, name: str = None) -> List[str]:
        """Get the user-defined extra flags for a specific tool/level combination."""
        if name is None:
            name = self.get_name()  # pylint: disable=assignment-from-no-return
        assert self.plugin_context is not None
        user_flags = self.plugin_context.config.get_tool_config(name, level, "flags")
        flags = []  # type: List[str]
        if user_flags:
            # See https://github.com/python/typeshed/issues/1476 for
            # justification to ignore.
            lex = shlex.shlex(user_flags, posix=True)  # type: ignore
            lex.whitespace_split = True
            flags = list(lex)
        return flags

    @staticmethod
    def is_valid_executable(path: str) -> bool:
        """
        Return whether a provided command exists and is executable.

        If the provided path has an extension on it, don't change it, otherwise
        try adding common extensions.
        """
        # On Windows, PATHEXT contains a list of extensions which can be
        # appended to a program name when searching PATH.
        extensions = os.environ.get("PATHEXT", None)
        _, path_ext = os.path.splitext(path)
        if path_ext or not extensions:
            return os.path.isfile(path) and os.access(path, os.X_OK)

        extensions_list = extensions.split(";")
        # Add "" (no extension) as a possibility.
        extensions_list.insert(0, "")
        for ext in extensions_list:
            extended_path = path + ext
            if os.path.isfile(extended_path) and os.access(extended_path, os.X_OK):
                return True

        return False

    @staticmethod
    def command_exists(command: str) -> bool:
        """Return whether a particular command is available on $PATH."""
        fpath, _ = os.path.split(command)

        if fpath:
            # Contains a path, not just a command, so don't search PATH
            return ToolPlugin.is_valid_executable(command)

        for path in os.environ["PATH"].split(os.pathsep):
            exe_path = os.path.join(path, command)
            if ToolPlugin.is_valid_executable(exe_path):
                return True

        return False
