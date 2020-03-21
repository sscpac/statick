"""Unit tests for the Java discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.java_discovery_plugin import JavaDiscoveryPlugin


def test_java_discovery_plugin_found():
    """Test that the plugin manager finds the Java discovery plugin."""
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
    # Verify that a plugin's get_name() function returns "java"
    assert any(
        plugin_info.plugin_object.get_name() == "java"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named Java Discovery Plugin
    assert any(
        plugin_info.name == "Java Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_java_discovery_plugin_scan_valid():
    """test that the java discovery plugin finds java source and class files."""
    jdp = JavaDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    jdp.scan(package, "level")
    expected_src = ["test.java", os.path.join("ignore_this", "ignoreme.java")]
    expected_bin = ["test.class", os.path.join("ignore_this", "IgnoreMe.class")]
    # We have to add the path to each of the above
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    expected_bin_fullpath = [
        os.path.join(package.path, filename) for filename in expected_bin
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["java_src"]) == set(expected_src_fullpath)
    assert set(package["java_bin"]) == set(expected_bin_fullpath)


def test_java_discovery_plugin_scan_invalid():
    """Test that the Java discovery plugin doesn't match non-Java files."""
    jdp = JavaDiscoveryPlugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    jdp.scan(package, "level")
    assert not package["java_src"]
    assert not package["java_bin"]


def test_java_discovery_plugin_scan_exceptions():
    """Test that the java discovery plugin properly respects exceptions."""
    jdp = JavaDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    jdp.scan(package, "level", exceptions)
    expected_src = ["test.java"]
    expected_bin = ["test.class"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    expected_bin_fullpath = [
        os.path.join(package.path, filename) for filename in expected_bin
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["java_src"]) == set(expected_src_fullpath)
    assert set(package["java_bin"]) == set(expected_bin_fullpath)
