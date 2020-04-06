"""Discover CSS files to analyze."""
from __future__ import print_function

import fnmatch
import os
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class CSSDiscoveryPlugin(DiscoveryPlugin):
    """Discover CSS files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "css"

    def scan(self, package, level, exceptions=None):
        """Scan package looking for CSS files."""
        src_files = []

        for root, _, files in os.walk(package.path):
            for f in fnmatch.filter(files, "*.css"):
                if not fnmatch.fnmatch(f, "*.min.css"):
                    full_path = os.path.join(root, f)
                    src_files.append(os.path.abspath(full_path))

        src_files = list(OrderedDict.fromkeys(src_files))

        print("  {} CSS source files found.".format(len(src_files)))
        if exceptions:
            original_file_count = len(src_files)
            src_files = exceptions.filter_file_exceptions_early(package, src_files)
            if original_file_count > len(src_files):
                print(
                    "  After filtering, {} CSS files will be scanned.".format(
                        len(src_files)
                    )
                )

        package["css_src"] = src_files
