"""Unit tests for the JavaScript discovery plugin."""

import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package

from statick_tool.plugins.discovery.javascript import JavaScriptDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_javascript_plugin_found():
    """Test that the plugin manager finds the JavaScript discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "javascript"
        for _, plugin in list(discovery_plugins.items())
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
    assert set(package["javascript_src"]) == set(expected_src_fullpath)
