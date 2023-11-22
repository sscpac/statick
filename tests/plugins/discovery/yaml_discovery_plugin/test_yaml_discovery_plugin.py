"""Unit tests for the YAML discovery plugin."""
import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.yaml import YAMLDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_yaml_discovery_plugin_found():
    """Test that the YAML discovery plugin is detected by the plugin system."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "yaml" for _, plugin in list(discovery_plugins.items())
    )


def test_yaml_discovery_plugin_scan_valid():
    """Test that the YAML discovery plugin correctly identifies YAML files."""
    ydp = YAMLDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    ydp.scan(package, "level")
    expected = ["test.yaml", "test.yml", os.path.join("ignore_this", "ignoreme.yaml")]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["yaml"]) == set(expected_fullpath)


def test_yaml_discovery_plugin_scan_invalid():
    """Test that the YAML discovery plugin doesn't identify non-YAML files."""
    ydp = YAMLDiscoveryPlugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    ydp.scan(package, "level")
    assert not package["yaml"]


def test_yaml_discovery_plugin_scan_exceptions():
    """Test that the yaml discovery plugin properly respects exceptions."""
    yamldp = YAMLDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    yamldp.scan(package, "level", exceptions)
    expected_src = ["test.yaml", "test.yml"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["yaml"]) == set(expected_src_fullpath)
