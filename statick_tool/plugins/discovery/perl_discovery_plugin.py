"""Discover C files to analyze."""

from __future__ import print_function
import os
import subprocess
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class CDiscoveryPlugin(DiscoveryPlugin):
    """Discover Perl files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "perl"

    def scan(self, package, level):
        """Scan package looking for Perl files."""
        perl_files = []
        perl_extensions = ('.pl')

        for root, _, files in os.walk(package.path):
            for f in files:
                if f.lower().endswith(perl_extensions):
                    full_path = os.path.join(root, f)
                    perl_files.append(os.path.abspath(full_path))
                else:
                    full_path = os.path.join(root, f)
                    output = subprocess.check_output(["file", full_path])
                    if "perl script" in output.lower():
                        perl_files.append(os.path.abspath(full_path))

        perl_files = list(OrderedDict.fromkeys(perl_files))

        print("  {} Perl files found.".format(len(perl_files)))

        package["perl_src"] = perl_files
