"""Discover python files to analyze."""

from __future__ import print_function

import fnmatch
import os
import subprocess
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin


class PythonDiscoveryPlugin(DiscoveryPlugin):
    """Discover python files to analyze."""

    def get_name(self):
        """Get name of discovery type."""
        return "python"

    def scan(self, package, level):
        """Scan package looking for python files."""
        python_files = []

        for root, _, files in os.walk(package.path):
            for f in fnmatch.filter(files, "*.py"):
                full_path = os.path.join(root, f)
                python_files.append(os.path.abspath(full_path))

            for f in files:
                full_path = os.path.join(root, f)
                output = subprocess.check_output(["file", full_path],
                                                 universal_newlines=True)
                if ("python script" in output or
                        "Python script" in output) and not \
                        f.endswith(".cfg"):
                    python_files.append(os.path.abspath(full_path))

        python_files = list(OrderedDict.fromkeys(python_files))

        print("  {} python files found.".format(len(python_files)))

        package["python_src"] = python_files
