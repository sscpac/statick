"""Unit tests for the rst discovery plugin."""
import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.rst import RstDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_rst_discovery_plugin_found():
    """Test that the plugin manager finds the rst discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "rst" for _, plugin in list(discovery_plugins.items())
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
