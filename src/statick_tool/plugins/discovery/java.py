"""Discover Java files to analyze."""
import logging
from collections import OrderedDict
from typing import List, Optional

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class JavaDiscoveryPlugin(DiscoveryPlugin):
    """Discover Java files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "java"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for java files."""
        java_src_files: List[str] = []
        java_class_files: List[str] = []

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".java"):
                java_src_files.append(file_dict["path"])
            if file_dict["name"].endswith(".class"):
                java_class_files.append(file_dict["path"])

        java_src_files = list(OrderedDict.fromkeys(java_src_files))
        java_class_files = list(OrderedDict.fromkeys(java_class_files))

        logging.info("  %d java source files found.", len(java_src_files))
        if exceptions:
            original_src_file_count = len(java_src_files)
            java_src_files = exceptions.filter_file_exceptions_early(
                package, java_src_files
            )
            if original_src_file_count > len(java_src_files):
                logging.info(
                    "  After filtering, %d java source files will be scanned.",
                    len(java_src_files),
                )

        logging.info("  %d java class files found.", len(java_class_files))
        if exceptions:
            original_class_file_count = len(java_class_files)
            java_class_files = exceptions.filter_file_exceptions_early(
                package, java_class_files
            )
            if original_class_file_count > len(java_class_files):
                logging.info(
                    "  After filtering, %d java class files will be scanned.",
                    len(java_class_files),
                )

        package["java_src"] = java_src_files
        package["java_bin"] = java_class_files
