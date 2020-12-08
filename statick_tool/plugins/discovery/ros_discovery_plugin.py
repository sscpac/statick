"""Discovery plugin to find ROS packages."""
import os
from typing import Optional

import xmltodict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class RosDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find ROS packages."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "ros"

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for ROS package files."""
        cmake_file = os.path.join(package.path, "CMakeLists.txt")
        package_file = os.path.join(package.path, "package.xml")
        ros_version = os.getenv("ROS_VERSION")

        if (
            os.path.isfile(cmake_file)
            and os.path.isfile(package_file)
            and ros_version is not None
        ):
            print("  Package is ROS{}.".format(ros_version))
            package["ros"] = True
            if ros_version == "1":
                package["catkin"] = True
            elif ros_version == "2":
                distro = os.getenv("ROS_DISTRO")
                path = os.getenv("PATH")
                if path is not None:
                    for item in path.split(":"):
                        if distro is not None and distro in item:
                            package[
                                "cmake_flags"
                            ] = "-DCMAKE_PREFIX_PATH=" + item.rstrip("/bin")
        elif os.path.isfile(package_file):
            with open(package_file) as fconfig:
                try:
                    output = xmltodict.parse(fconfig.read())
                except xmltodict.expat.ExpatError as exc:
                    # No valid XML found, so we are not going to find the build type.
                    package["ros"] = False
                    print("  Invalid XML in {}: {}".format(package_file, exc))
                    return
                if (
                    "package" in output
                    and "export" in output["package"]
                    and "build_type" in output["package"]["export"]
                    and output["package"]["export"]["build_type"] == "ament_python"
                ):
                    print("  Package is ROS{}.".format(ros_version))
                    package["ros"] = True
        else:
            print("  Package is not ROS.")
            package["ros"] = False
