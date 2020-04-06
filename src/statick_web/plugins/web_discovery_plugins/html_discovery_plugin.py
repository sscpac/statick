"""Discover HTML files to analyze."""

from __future__ import print_function

import fnmatch
import os
import subprocess
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
        globs = ["*.html"]

        file_cmd_exists = True
        if not DiscoveryPlugin.file_command_exists():
            file_cmd_exists = False

        root = ""
        files = []
        for root, _, files in os.walk(package.path):
            for glob in globs:
                for f in fnmatch.filter(files, glob):
                    full_path = os.path.join(root, f)
                    src_files.append(os.path.abspath(full_path))

            if file_cmd_exists:
                for f in files:
                    full_path = os.path.join(root, f)
                    output = subprocess.check_output(
                        ["file", full_path], universal_newlines=True
                    )
                    # pylint: disable=unsupported-membership-test
                    if "HTML document" in output:
                        # pylint: enable=unsupported-membership-test
                        src_files.append(os.path.abspath(full_path))

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
