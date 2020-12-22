"""Discover HTML files to analyze."""

from __future__ import print_function

from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class HTMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover HTML files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "html"

    def scan(self, package, level, exceptions=None):
        """Scan package looking for HTML files."""
        src_files = []

        self.find_files(package)

        for file_dict in package.files.values():
            if (
                file_dict["name"].endswith(".html")
                or "html document" in file_dict["file_cmd_out"]
            ):
                src_files.append(file_dict["path"])

        src_files = list(OrderedDict.fromkeys(src_files))

        print("  {} HTML source files found.".format(len(src_files)))
        if exceptions:
            original_file_count = len(src_files)
            src_files = exceptions.filter_file_exceptions_early(package, src_files)
            if original_file_count > len(src_files):
                print(
                    "  After filtering, {} HTML files will be scanned.".format(
                        len(src_files)
                    )
                )

        package["html_src"] = src_files
