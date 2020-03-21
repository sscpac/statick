"""Unit tests for the catkin discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.catkin_discovery_plugin import CatkinDiscoveryPlugin


def test_catkin_discovery_plugin_found():
    """Test that the plugin manager can find the Catkin plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {"Discovery": DiscoveryPlugin,}
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "catkin"
    assert any(
        plugin_info.plugin_object.get_name() == "catkin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named Catkin Discovery Plugin
    assert any(
        plugin_info.name == "Catkin Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_catkin_discovery_plugin_scan_valid():
    """Test the behavior when the Catkin plugin scans a valid package."""
    cdp = CatkinDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    cdp.scan(package, "level")
    assert package["catkin"]


def test_catkin_discovery_plugin_scan_invalid_badpath():
    """Test the behavior when the Catkin plugin scans a nonexistent directory."""
    cdp = CatkinDiscoveryPlugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    cdp.scan(package, "level")
    assert not package["catkin"]


def test_catkin_discovery_plugin_scan_invalid_nocmake():
    """Test the behavior when the Catkin plugin scans a directory with no CMakeLists.txt."""
    cdp = CatkinDiscoveryPlugin()
    package = Package(
        "invalid_package_nocmakelists",
        os.path.join(os.path.dirname(__file__), "invalid_package_nocmakelists"),
    )
    cdp.scan(package, "level")
    assert not package["catkin"]


def test_catkin_discovery_plugin_scan_invalid_packagexml():
    """Test the behavior when the Catkin plugin scans a directory with no package.xml."""
    cdp = CatkinDiscoveryPlugin()
    package = Package(
        "invalid_package_nopackagexml",
        os.path.join(os.path.dirname(__file__), "invalid_package_nopackagexml"),
    )
    cdp.scan(package, "level")
    assert not package["catkin"]
