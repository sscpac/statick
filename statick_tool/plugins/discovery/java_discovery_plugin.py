"""Discover Java files to analyze."""

from __future__ import print_function

import fnmatch
import os
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class JavaDiscoveryPlugin(DiscoveryPlugin):
    """Discover Java files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "java"

    def scan(self, package, level):
        """Scan package looking for java files."""
        java_src_files = []
        java_class_files = []

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
        print("  {} java class files found.".format(len(java_class_files)))

        package["java_src"] = java_src_files
        package["java_bin"] = java_class_files
