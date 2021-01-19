"""Discover JavaScript files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class JavaScriptDiscoveryPlugin(DiscoveryPlugin):
    """Discover JavaScript files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "javascript"

    def scan(self, package, level, exceptions=None):
        """Scan package looking for JavaScript files."""
        src_files = []

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".js") and not file_dict["name"].endswith(
                ".min.js"
            ):
                src_files.append(file_dict["path"])

        src_files = list(OrderedDict.fromkeys(src_files))

        logging.info("  %d JavaScript source files found.", len(src_files))
        if exceptions:
            original_file_count = len(src_files)
            src_files = exceptions.filter_file_exceptions_early(package, src_files)
            if original_file_count > len(src_files):
                logging.info(
                    "  After filtering, %d Javascript files will be scanned.",
                    len(src_files),
                )

        package["javascript_src"] = src_files
