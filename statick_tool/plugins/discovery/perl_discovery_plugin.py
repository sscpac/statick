"""Discover Perl files to analyze."""
import fnmatch
import os
import subprocess
from collections import OrderedDict
from typing import List, Optional

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PerlDiscoveryPlugin(DiscoveryPlugin):
    """Discover Perl files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "perl"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for Perl files."""
        perl_files = []  # type: List[str]

        self.scan_once(package, level, exceptions)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".pl") or "perl script" in file_dict["file_cmd_out"].lower():
                perl_files.append(file_dict["path"])

        perl_files = list(OrderedDict.fromkeys(perl_files))
        print(perl_files)

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
