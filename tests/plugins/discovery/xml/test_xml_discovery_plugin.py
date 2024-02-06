"""Unit tests for the XML discovery plugin."""

import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.xml import XMLDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_xml_discovery_plugin_found():
    """Test that the XML discovery plugin is detected by the plugin system."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "xml" for _, plugin in list(discovery_plugins.items())
    )


def test_xml_discovery_plugin_scan_valid():
    """Test that the XML discovery plugin correctly identifies XML files."""
    xmldp = XMLDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    xmldp.scan(package, "level")
    expected = ["test.xml", "test.launch", os.path.join("ignore_this", "ignoreme.xml")]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["xml"]) == set(expected_fullpath)


def test_xml_discovery_plugin_scan_invalid():
    """Text that the XML discovery plugin doesn't identify non-XML files."""
    xmldp = XMLDiscoveryPlugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    xmldp.scan(package, "level")
    assert not package["xml"]


def test_xml_discovery_plugin_scan_exceptions():
    """Test that the xml discovery plugin properly respects exceptions."""
    xmldp = XMLDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    xmldp.scan(package, "level", exceptions)
    expected_src = ["test.xml", "test.launch"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["xml"]) == set(expected_src_fullpath)
