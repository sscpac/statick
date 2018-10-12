"""Discover C files to analyze."""

from __future__ import print_function

import os
import subprocess
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class CDiscoveryPlugin(DiscoveryPlugin):
    """Discover C/C++ files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "C"

    def scan(self, package, level):
        """Scan package looking for C files."""
        c_files = []
        c_extensions = ('.c', '.cc', '.cpp', '.cxx', '.h', '.hxx', '.hpp')

        for root, _, files in os.walk(package.path):
            for f in files:
                if f.lower().endswith(c_extensions):
                    full_path = os.path.join(root, f)
                    c_files.append(os.path.abspath(full_path))
                else:
                    full_path = os.path.join(root, f)
                    output = subprocess.check_output(["file", full_path], universal_newlines=True)
                    if ("c source" in output.lower() or
                            "c++ source" in output.lower()) and not \
                            f.endswith(".cfg"):
                        c_files.append(os.path.abspath(full_path))

        c_files = list(OrderedDict.fromkeys(c_files))

        print("  {} C/C++ files found.".format(len(c_files)))

        package["c_src"] = c_files
