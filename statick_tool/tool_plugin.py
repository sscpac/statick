"""Tool plugin."""
import argparse
import logging
import os
import shlex
from typing import Any, Dict, List, Optional, Union

from yapsy.IPlugin import IPlugin

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


# No stubs available for IPlugin so ignoring type.
class ToolPlugin(IPlugin):  # type: ignore
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

    def get_file_types(self) -> List[str]:
        """Return a list of file types the plugin can scan."""

    def scan(self, package: Package, level: str) -> Optional[List[Issue]]:
        """Run tool and gather output."""
        files: List[str] = []
        for file_type in self.get_file_types():
            if file_type in package:
                files += package[file_type]

        if files:
            total_output = self.process_files(package, level, files, self.get_user_flags(level))
            if total_output:
                if self.plugin_context and self.plugin_context.args.output_directory:
                    with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                        for output in total_output:
                            fid.write(output)
                return self.parse_output(total_output)
            else:
                return None
        else:
            return None

    def process_files(self, package: Package, level: str, files: List[str], user_flags: List[str]) -> Optional[List[str]]:
        """Run tool and gather output."""

    def parse_output(self, total_output: List[str]) -> List[Issue]:
        """Parse tool output and report issues."""

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Set the plugin context."""
        self.plugin_context = plugin_context

    def load_mapping(self) -> Dict[str, str]:
        """Load a mapping between warnings and identifiers."""
        file_name: str = f"plugin_mapping/{self.get_name()}.txt"
        assert self.plugin_context is not None
        full_path: Union[Any, str, None] = self.plugin_context.resources.get_file(
            file_name
        )
        if (
            "mapping_file_suffix" in self.plugin_context.args
            and self.plugin_context.args.mapping_file_suffix is not None
        ):
            # If the user specified a suffix, try to get the suffixed version of the
            # file.
            suffixed_file_name = (
                f"plugin_mapping/{self.get_name()}-"
                f"{self.plugin_context.args.mapping_file_suffix}.txt"
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
        warning_mapping: Dict[str, str] = {}
        with open(full_path, "r", encoding="utf8") as mapping_file:
            for line in mapping_file.readlines():
                split_line = line.strip().split(":")
                if len(split_line) != 2:
                    logging.warning(
                        "Invalid line %s in mapping file %s", line, file_name
                    )
                    continue
                warning_mapping[split_line[0]] = split_line[1]
        return warning_mapping

    def get_user_flags(self, level: str, name: Optional[str] = None) -> List[str]:
        """Get the user-defined extra flags for a specific tool/level combination."""
        if name is None:
            name = self.get_name()  # pylint: disable=assignment-from-no-return
        assert self.plugin_context is not None
        user_flags = self.plugin_context.config.get_tool_config(name, level, "flags")
        flags: List[str] = []
        if user_flags:
            # See https://github.com/python/typeshed/issues/1476 for
            # justification to ignore.
            lex = shlex.shlex(user_flags, posix=True)
            lex.whitespace_split = True
            flags = list(lex)
        return flags

    @staticmethod
    def is_valid_executable(path: str) -> bool:
        """Return whether a provided command exists and is executable.

        If the provided path has an extension on it, don't change it, otherwise try
        adding common extensions.
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
