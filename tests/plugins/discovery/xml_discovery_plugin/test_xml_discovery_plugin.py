"""Unit tests for the XML discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.xml_discovery_plugin import XMLDiscoveryPlugin


def test_xml_discovery_plugin_found():
    """Test that the XML discovery plugin is detected by the plugin system."""
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
    # Verify that a plugin's get_name() function returns "xml"
    assert any(
        plugin_info.plugin_object.get_name() == "xml"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named XML Discovery Plugin
    assert any(
        plugin_info.name == "XML Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
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
