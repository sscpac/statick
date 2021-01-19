"""Discovery plugin to find catkin packages."""
import logging
import os
from typing import Optional

from deprecated import deprecated

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class CatkinDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find catkin packages."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "catkin"

    @deprecated(
        "This plugin has been deprecated since v0.4.6. A more generic version of this plugin is the ros_discovery_plugin. This plugin will be removed in v0.6."  # NOLINT
    )
    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for catkin files."""
        cmake_file = os.path.join(package.path, "CMakeLists.txt")
        package_file = os.path.join(package.path, "package.xml")

        if os.path.isfile(cmake_file) and os.path.isfile(package_file):
            logging.info("  Package is catkin.")
            package["catkin"] = True
        else:
            logging.info("  Package is not catkin.")
            package["catkin"] = False
