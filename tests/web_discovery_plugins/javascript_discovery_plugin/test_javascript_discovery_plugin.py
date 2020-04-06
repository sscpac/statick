"""Unit tests for the JavaScript discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.javascript_discovery_plugin import (
    JavaScriptDiscoveryPlugin,
)


def test_javascript_plugin_found():
    """Test that the plugin manager finds the JavaScript discovery plugin."""
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
    # Verify that a plugin's get_name() function returns "javascript"
    assert any(
        plugin_info.plugin_object.get_name() == "javascript"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named javascript Discovery Plugin
    assert any(
        plugin_info.name == "JavaScript Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_javascript_plugin_scan_valid():
    """Test that the JavaScript discovery plugin finds valid JavaScript source files."""
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    discovery_plugin = JavaScriptDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    expected = ["test.js", os.path.join("ignore_this", "ignoreme.js")]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["javascript_src"]) == set(expected_fullpath)


def test_javascript_plugin_scan_invalid():
    """Test that the JavaScript discovery plugin doesn't find non-JavaScript files."""
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    discovery_plugin = JavaScriptDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    assert not package["javascript_src"]


def test_javascript_discovery_plugin_scan_exceptions():
    """Test that the JavaScript discovery plugin properly respects exceptions."""
    discovery_plugin = JavaScriptDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    discovery_plugin.scan(package, "level", exceptions)
    expected_src = ["test.js"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    # Neat trick to verify that two unordered lists are the same
    print("package: {}".format(package["javascript_src"]))
    assert set(package["javascript_src"]) == set(expected_src_fullpath)
