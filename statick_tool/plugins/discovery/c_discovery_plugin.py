"""Discover C files to analyze."""
import os
import subprocess
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class CDiscoveryPlugin(DiscoveryPlugin):
    """Discover C/C++ files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "C"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for C files."""
        c_files = []  # type: List[str]
        c_extensions = (".c", ".cc", ".cpp", ".cxx", ".h", ".hxx", ".hpp")
        file_cmd_exists = True  # type: bool
        if not DiscoveryPlugin.file_command_exists():
            file_cmd_exists = False

        for root, _, files in os.walk(package.path):
            for f in files:
                if f.lower().endswith(c_extensions):
                    full_path = os.path.join(root, f)
                    c_files.append(os.path.abspath(full_path))
                elif file_cmd_exists:
                    full_path = os.path.join(root, f)
                    output = subprocess.check_output(
                        ["file", full_path], universal_newlines=True
                    )  # type: str
                    if (
                        "c source" in output.lower()
                        or "c program" in output.lower()
                        or "c++ source" in output.lower()
                    ) and not f.endswith(".cfg"):
                        c_files.append(os.path.abspath(full_path))

        c_files = list(OrderedDict.fromkeys(c_files))

        print("  {} C/C++ files found.".format(len(c_files)))
        if exceptions:
            original_file_count = len(c_files)
            c_files = exceptions.filter_file_exceptions_early(package, c_files)
            if original_file_count > len(c_files):
                print(
                    "  After filtering, {} C/C++ files will be scanned.".format(
                        len(c_files)
                    )
                )

        package["c_src"] = c_files
