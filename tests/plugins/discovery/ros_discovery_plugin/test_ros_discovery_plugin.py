"""Unit tests for the ROS discovery plugin."""
import contextlib
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.ros_discovery_plugin import RosDiscoveryPlugin


# From https://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment
@contextlib.contextmanager
def modified_environ(*remove, **update):
    """Temporarily updates the ``os.environ`` dictionary in-place.

    The ``os.environ`` dictionary is updated in-place so that the modification
    is sure to work in all situations.
    :param remove: Environment variables to remove.
    :param update: Dictionary of environment variables and values to add/update.
    """
    env = os.environ
    update = update or {}
    remove = remove or []

    # List of environment variables being updated or removed.
    stomped = (set(update.keys()) | set(remove)) & set(env.keys())
    # Environment variables and values to restore on exit.
    update_after = {k: env[k] for k in stomped}
    # Environment variables and values to remove on exit.
    remove_after = frozenset(k for k in update if k not in env)

    try:
        env.update(update)
        [env.pop(k, None) for k in remove]
        yield
    finally:
        env.update(update_after)
        [env.pop(k) for k in remove_after]


def test_ros_discovery_plugin_found():
    """Test that the plugin manager can find the ROS plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {
            "Discovery": DiscoveryPlugin,
        }
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "ros"
    assert any(
        plugin_info.plugin_object.get_name() == "ros"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named ROS Discovery Plugin
    assert any(
        plugin_info.name == "ROS Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_ros_discovery_plugin_scan_valid():
    """Test the behavior when the ROS plugin scans a valid package."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    os.environ["ROS_VERSION"] = "1"
    rdp.scan(package, "level")
    assert "is_ros1" in package


def test_ros_discovery_plugin_scan_ros2_python_only():
    """Test the behavior when the ROS plugin scans a valid Python-only package."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "ros2_python_package",
        os.path.join(os.path.dirname(__file__), "ros2_python_package"),
    )
    os.environ["ROS_VERSION"] = "2"
    rdp.scan(package, "level")
    assert "is_ros2" in package


def test_ros_discovery_plugin_scan_invalid_no_ros_distro():
    """Test the behavior when the ROS plugin scans a valid package but no ROS
    environment has been set."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    del os.environ["ROS_VERSION"]
    rdp.scan(package, "level")
    assert "is_ros1" not in package
    assert "is_ros2" not in package


def test_ros_discovery_plugin_scan_invalid_badpath():
    """Test the behavior when the ROS plugin scans a nonexistent directory."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    os.environ["ROS_VERSION"] = "1"
    rdp.scan(package, "level")
    assert "is_ros1" not in package


def test_ros_discovery_plugin_scan_invalid_nocmake():
    """Test the behavior when the ROS plugin scans a directory with no
    CMakeLists.txt."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "invalid_package_nocmakelists",
        os.path.join(os.path.dirname(__file__), "invalid_package_nocmakelists"),
    )
    os.environ["ROS_VERSION"] = "1"
    rdp.scan(package, "level")
    assert "is_ros1" not in package
    assert "is_ros2" not in package


def test_ros_discovery_plugin_scan_invalid_packagexml():
    """Test the behavior when the ROS plugin scans a directory with no
    package.xml."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "invalid_package_nopackagexml",
        os.path.join(os.path.dirname(__file__), "invalid_package_nopackagexml"),
    )
    os.environ["ROS_VERSION"] = "1"
    rdp.scan(package, "level")
    assert "is_ros1" not in package
    assert "is_ros2" not in package


def test_ros_discovery_plugin_ros2_scan_valid():
    """Test the behavior when the ROS plugin scans a valid package in a ROS2
    environment."""
    path = os.getenv("PATH")
    if "ros" not in path:
        path = path + ":/opt/ros/foxy/bin"
    with modified_environ(PATH=path):
        rdp = RosDiscoveryPlugin()
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        os.environ["ROS_VERSION"] = "2"
        os.environ["ROS_DISTRO"] = "foxy"
        rdp.scan(package, "level")
        assert "is_ros2" in package


def test_ros_discovery_plugin_ros1_scan_valid():
    """Test the behavior when the ROS plugin scans a valid package in a ROS1
    environment."""
    rdp = RosDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    os.environ["ROS_VERSION"] = "1"
    rdp.scan(package, "level")
    assert "is_ros1" in package
