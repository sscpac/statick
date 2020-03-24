"""Discover Java files to analyze."""
import fnmatch
import os
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class JavaDiscoveryPlugin(DiscoveryPlugin):
    """Discover Java files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "java"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for java files."""
        java_src_files = []  # type: List[str]
        java_class_files = []  # type: List[str]

        for root, _, files in os.walk(package.path):
            for f in fnmatch.filter(files, "*.java"):
                full_path = os.path.join(root, f)
                java_src_files.append(os.path.abspath(full_path))

            for f in fnmatch.filter(files, "*.class"):
                full_path = os.path.join(root, f)
                java_class_files.append(os.path.abspath(full_path))

        java_src_files = list(OrderedDict.fromkeys(java_src_files))
        java_class_files = list(OrderedDict.fromkeys(java_class_files))

        print("  {} java source files found.".format(len(java_src_files)))
        if exceptions:
            original_src_file_count = len(java_src_files)
            java_src_files = exceptions.filter_file_exceptions_early(
                package, java_src_files
            )
            if original_src_file_count > len(java_src_files):
                print(
                    "  After filtering, {} java source files will be scanned.".format(
                        len(java_src_files)
                    )
                )

        print("  {} java class files found.".format(len(java_class_files)))
        if exceptions:
            original_class_file_count = len(java_class_files)
            java_class_files = exceptions.filter_file_exceptions_early(
                package, java_class_files
            )
            if original_class_file_count > len(java_class_files):
                print(
                    "  After filtering, {} java class files will be scanned.".format(
                        len(java_class_files)
                    )
                )

        package["java_src"] = java_src_files
        package["java_bin"] = java_class_files
