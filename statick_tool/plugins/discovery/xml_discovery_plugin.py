"""Discover XML files to analyze."""
import fnmatch
import os
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class XMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover XML files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "xml"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for XML files."""
        xml_files = []  # type: List[str]
        globs = ["*.xml", "*.launch"]  # type: List[str]

        root = ""
        for root, _, files in os.walk(package.path):
            for glob in globs:
                for f in fnmatch.filter(files, glob):
                    full_path = os.path.join(root, f)
                    xml_files.append(os.path.abspath(full_path))

        xml_files = list(OrderedDict.fromkeys(xml_files))

        print("  {} XML files found.".format(len(xml_files)))
        if exceptions:
            original_file_count = len(xml_files)
            xml_files = exceptions.filter_file_exceptions_early(package, xml_files)
            if original_file_count > len(xml_files):
                print(
                    "  After filtering, {} XML files will be scanned.".format(
                        len(xml_files)
                    )
                )

        package["xml"] = xml_files
