"""Discovery plugin to find catkin packages."""

from __future__ import print_function

import os

from statick_tool.discovery_plugin import DiscoveryPlugin


class CatkinDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find catkin packages."""

    def get_name(self):
        """Get name of discovery type."""
        return "catkin"

    def scan(self, package, level, exceptions=None):
        """Scan package looking for catkin files."""
        cmake_file = os.path.join(package.path, "CMakeLists.txt")
        package_file = os.path.join(package.path, "package.xml")

        if os.path.isfile(cmake_file) and os.path.isfile(package_file):
            print("  Package is catkin.")
            package["catkin"] = True
        else:
            print("  Package is not catkin.")
            package["catkin"] = False
