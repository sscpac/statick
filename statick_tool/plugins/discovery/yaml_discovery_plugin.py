"""Discover YAML files to analyze."""
from collections import OrderedDict
from typing import List, Optional

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class YAMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover YAML files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "yaml"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for YAML files."""
        yaml_files = []  # type: List[str]

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".yaml"):
                yaml_files.append(file_dict["path"])

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
