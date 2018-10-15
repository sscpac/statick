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

    def scan(self, package, level):
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

        package["xml"] = xml_files
