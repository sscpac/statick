"""Discover YAML files to analyze."""
import fnmatch
import os
from collections import OrderedDict
from typing import List

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class YAMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover YAML files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "yaml"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for YAML files."""
        yaml_files = []  # type: List[str]
        globs = ["*.yaml"]  # type: List[str]

        root = ""
        for root, _, files in os.walk(package.path):
            for glob in globs:
                for f in fnmatch.filter(files, glob):
                    full_path = os.path.join(root, f)
                    yaml_files.append(os.path.abspath(full_path))

        yaml_files = list(OrderedDict.fromkeys(yaml_files))

        print("  {} YAML files found.".format(len(yaml_files)))
        if exceptions:
            original_file_count = len(yaml_files)
            yaml_files = exceptions.filter_file_exceptions_early(package, yaml_files)
            if original_file_count > len(yaml_files):
                print(
                    "  After filtering, {} YAML files will be scanned.".format(
                        len(yaml_files)
                    )
                )

        package["yaml"] = yaml_files
