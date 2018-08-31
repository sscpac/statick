"""Discover YAML files to analyze."""

from __future__ import print_function
import os
import fnmatch
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class YAMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover YAML files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "yaml"

    def scan(self, package, level):
        """Scan package looking for YAML files."""
        yaml_files = []
        globs = ["*.yaml"]

        root = ''
        files = []
        for root, _, files in os.walk(package.path):
            for glob in globs:
                for f in fnmatch.filter(files, glob):
                    full_path = os.path.join(root, f)
                    yaml_files.append(os.path.abspath(full_path))

        yaml_files = list(OrderedDict.fromkeys(yaml_files))

        print("  {} YAML files found.".format(len(yaml_files)))

        package["yaml"] = yaml_files
