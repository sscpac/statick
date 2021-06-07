"""Unit tests for the rst discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.rst_discovery_plugin import RstDiscoveryPlugin


def test_rst_discovery_plugin_found():
    """Test that the plugin manager finds the rst discovery plugin."""
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
    # Verify that a plugin's get_name() function returns "rst"
    assert any(
        plugin_info.plugin_object.get_name() == "rst"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named rst Discovery Plugin
    assert any(
        plugin_info.name == "rst Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_rst_discovery_plugin_scan_valid():
    """Test that the rst discovery plugin finds valid rst source and bib files."""
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    discovery_plugin = RstDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    expected = ["test.rst", os.path.join("ignore_this", "ignoreme.rst")]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["rst_src"]) == set(expected_fullpath)


def test_rst_discovery_plugin_scan_invalid():
    """Test that the rst discovery plugin doesn't find non-rst files."""
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    discovery_plugin = RstDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    assert not package["rst_src"]


def test_rst_discovery_plugin_scan_exceptions():
    """Test that the rst discovery plugin properly respects exceptions."""
    discovery_plugin = RstDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    discovery_plugin.scan(package, "level", exceptions)
    expected = ["test.rst"]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    print("package: {}".format(package["rst_src"]))
    assert set(package["rst_src"]) == set(expected_fullpath)


def test_rst_discovery_plugin_no_file_cmd(monkeypatch):
    """
    Test when file command does not exist.

    Test that files are not discovered with file command output if file
    command does not exist.
    """
    monkeypatch.setenv("PATH", "")
    discovery_plugin = RstDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    discovery_plugin.scan(package, "level")
    expected = ["test.rst", os.path.join("ignore_this", "ignoreme.rst")]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["rst_src"]) == set(expected_fullpath)
