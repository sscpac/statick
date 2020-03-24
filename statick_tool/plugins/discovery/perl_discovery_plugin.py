"""Discover Perl files to analyze."""
import fnmatch
import os
import subprocess
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PerlDiscoveryPlugin(DiscoveryPlugin):
    """Discover Perl files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "perl"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for Perl files."""
        perl_files = []  # type: List[str]

        file_cmd_exists = True  # type: bool
        if not DiscoveryPlugin.file_command_exists():
            file_cmd_exists = False

        for root, _, files in os.walk(package.path):
            for f in fnmatch.filter(files, "*.pl"):
                full_path = os.path.join(root, f)
                perl_files.append(os.path.abspath(full_path))

            if file_cmd_exists:
                for f in files:
                    full_path = os.path.join(root, f)
                    output = subprocess.check_output(
                        ["file", full_path], universal_newlines=True
                    )  # type: str
                    if "perl script" in output.lower():
                        perl_files.append(os.path.abspath(full_path))

        perl_files = list(OrderedDict.fromkeys(perl_files))

        print("  {} Perl files found.".format(len(perl_files)))
        if exceptions:
            original_file_count = len(perl_files)
            perl_files = exceptions.filter_file_exceptions_early(package, perl_files)
            if original_file_count > len(perl_files):
                print(
                    "  After filtering, {} perl files will be scanned.".format(
                        len(perl_files)
                    )
                )

        package["perl_src"] = perl_files
