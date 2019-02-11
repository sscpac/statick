"""Discover XML files to analyze."""

from __future__ import print_function

import fnmatch
import os
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class XMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover XML files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "xml"

    def scan(self, package, level, exceptions=None):
        """Scan package looking for XML files."""
        xml_files = []
        globs = ["*.xml", "*.launch"]

        root = ''
        files = []
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
                print("  After filtering, {} XML files will be scanned.".format(len(xml_files)))

        package["xml"] = xml_files
