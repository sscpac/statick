"""Discover python files to analyze."""
import fnmatch
import os
import subprocess
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PythonDiscoveryPlugin(DiscoveryPlugin):
    """Discover python files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "python"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for python files."""
        python_files = []  # type: List[str]

        file_cmd_exists = True  # type: bool
        if not DiscoveryPlugin.file_command_exists():
            file_cmd_exists = False

        for root, _, files in os.walk(package.path):
            for f in fnmatch.filter(files, "*.py"):
                full_path = os.path.join(root, f)
                python_files.append(os.path.abspath(full_path))

            if file_cmd_exists:
                for f in files:
                    full_path = os.path.join(root, f)
                    output = subprocess.check_output(
                        ["file", full_path], universal_newlines=True
                    )  # type: str
                    # pylint: disable=unsupported-membership-test
                    if (
                        "python script" in output or "Python script" in output
                    ) and not f.endswith(".cfg"):
                        # pylint: enable=unsupported-membership-test
                        python_files.append(os.path.abspath(full_path))

        python_files = list(OrderedDict.fromkeys(python_files))

        print("  {} python files found.".format(len(python_files)))
        if exceptions:
            original_file_count = len(python_files)
            python_files = exceptions.filter_file_exceptions_early(
                package, python_files
            )
            if original_file_count > len(python_files):
                print(
                    "  After filtering, {} python files will be scanned.".format(
                        len(python_files)
                    )
                )

        package["python_src"] = python_files
