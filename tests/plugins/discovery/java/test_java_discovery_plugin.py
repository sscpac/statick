"""Unit tests for the Java discovery plugin."""

import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.java import JavaDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_java_discovery_plugin_found():
    """Test that the plugin manager finds the Java discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "java" for _, plugin in list(discovery_plugins.items())
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
