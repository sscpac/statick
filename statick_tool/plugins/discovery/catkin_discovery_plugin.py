"""Discovery plugin to find catkin packages."""
import os

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class CatkinDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find catkin packages."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "catkin"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for catkin files."""
        cmake_file = os.path.join(package.path, "CMakeLists.txt")
        package_file = os.path.join(package.path, "package.xml")

        if os.path.isfile(cmake_file) and os.path.isfile(package_file):
            print("  Package is catkin.")
            package["catkin"] = True
        else:
            print("  Package is not catkin.")
            package["catkin"] = False
