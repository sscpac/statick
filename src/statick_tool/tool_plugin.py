"""Tool plugin."""

import argparse
import logging
import os
import re
import shlex
import subprocess
from typing import Any, Match, Optional, Pattern, Union

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class ToolPlugin:
    """Default implementation of tool plugin."""

    plugin_context = None

    def get_name(self) -> str:  # type: ignore[empty-body]
        """Get name of tool."""
        pass  # pylint: disable=unnecessary-pass

    @classmethod
    def get_tool_dependencies(cls) -> list[str]:
        """Get a list of tools that must run before this one."""
        return []

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments."""

    def get_file_types(self) -> list[str]:  # type: ignore[empty-body]
        """Return a list of file types the plugin can scan."""

    def get_binary(  # pylint: disable=unused-argument
        self, level: Optional[str] = None, package: Optional[Package] = None
    ) -> str:
        """Get tool binary name."""
        return None

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed.

        If no version is found the function returns "Unknown".
        """
        tool_bin = self.get_binary()  # pylint: disable=assignment-from-none
        if tool_bin is None:
            return "Unknown"

        try:
            output = subprocess.check_output(
                [tool_bin, "--version"], stderr=subprocess.STDOUT
            )
            return output.decode("utf-8")
        except subprocess.CalledProcessError as e:  # NOLINT
            return "Unknown"
        except FileNotFoundError as e:  # NOLINT
            return "Uninstalled"

    def get_version_from_apt(self) -> str:
        """Figure out and return the version of the tool that's installed by apt.

        If no version is found the function returns "Uninstalled".
        """
        version = "Uninstalled"

        output = subprocess.check_output(
            ["dpkg", "-l"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        ver_re = rf"(.+{self.get_binary()}.*)"
        parse: Pattern[str] = re.compile(ver_re)
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match:
                return line
        return version

    def get_version_from_docker(self) -> str:
        """Figure out and return the version of the tool that's installed by docker.

        If no version is found the function returns "Uninstalled".
        """
        version = "Uninstalled"

        output = subprocess.check_output(
            ["docker", "image", "list"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        ver_re = rf"(.+{self.get_binary()}.*)"
        parse: Pattern[str] = re.compile(ver_re)
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match:
                return line
        return version

    def get_version_from_npm(self, is_global=True) -> str:
        """Figure out and return the version of the tool that's installed by npm.

        If no version is found the function returns "Uninstalled".
        """
        version = "Uninstalled"

        if is_global:
            global_flag = "-g"
        else:
            global_flag = ""

        output = subprocess.check_output(
            ["npm", global_flag, "list"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        ver_re = rf"(.+{self.get_binary()}.*)@([0-9]*\.?[0-9]+\.?[0-9]+)"
        parse: Pattern[str] = re.compile(ver_re)
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match:
                version = match.group(2)
                return version
        return version

    def scan(self, package: Package, level: str) -> Optional[list[Issue]]:
        """Run tool and gather output."""
        files: list[str] = []
        for file_type in self.get_file_types():
            if file_type in package and package[file_type]:
                files += package[file_type]

        if files:
            total_output = (  # pylint: disable=assignment-from-no-return
                self.process_files(package, level, files, self.get_user_flags(level))
            )
            if total_output is not None:
                if self.plugin_context and self.plugin_context.args.output_directory:
                    with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                        for output in total_output:
                            fid.write(output)

                return self.parse_output(total_output, package)

            return None

        return []

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output."""

    def parse_output(  # type: ignore[empty-body]
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Set the plugin context."""
        self.plugin_context = plugin_context

    def load_mapping(self) -> dict[str, str]:
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
        warning_mapping: dict[str, str] = {}
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

    def get_user_flags(self, level: str, name: Optional[str] = None) -> list[str]:
        """Get the user-defined extra flags for a specific tool/level combination."""
        if name is None:
            name = self.get_name()  # pylint: disable=assignment-from-no-return
        assert self.plugin_context is not None
        user_flags = self.plugin_context.config.get_tool_config(name, level, "flags")
        flags: list[str] = []
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
