"""Discover XML files to analyze."""
from collections import OrderedDict
from typing import List, Optional, Tuple

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class XMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover XML files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "xml"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for XML files."""
        xml_files = []  # type: List[str]
        xml_extensions = (".xml", ".launch")  # type: Tuple[str, str]

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(xml_extensions):
                xml_files.append(file_dict["path"])

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
