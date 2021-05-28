"""Unit tests for the HTML discovery plugin."""

import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.html_discovery_plugin import HTMLDiscoveryPlugin


def test_html_plugin_found():
    """Test that the plugin manager finds the html discovery plugin."""
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
    # Verify that a plugin's get_name() function returns "html"
    assert any(
        plugin_info.plugin_object.get_name() == "html"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named html Discovery Plugin
    assert any(
        plugin_info.name == "HTML Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_html_plugin_no_file_cmd():
    """Test that the html discovery plugin finds valid html source files even with no file cmd."""
    old_env = dict(os.environ)

    try:
        # the next line removes the file command (and pretty much everything) from the PATH environment variable
        os.environ.update({"PATH": os.path.dirname(__file__)})
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        discovery_plugin = HTMLDiscoveryPlugin()
        discovery_plugin.scan(package, "level")
        expected = ["test.html", os.path.join("ignore_this", "ignoreme.html")]
        assert not discovery_plugin.file_command_exists()
        # We have to add the path to each of the above...yuck
        expected_fullpath = [
            os.path.join(package.path, filename) for filename in expected
        ]
        # Neat trick to verify that two unordered lists are the same
        assert set(package["html_src"]) == set(expected_fullpath)
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_html_plugin_scan_valid():
    """Test that the html discovery plugin finds valid html source files."""
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    discovery_plugin = HTMLDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    expected = ["test.html", os.path.join("ignore_this", "ignoreme.html")]
    if discovery_plugin.file_command_exists():
        expected += ["oddextensionhtml.source"]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["html_src"]) == set(expected_fullpath)


def test_html_plugin_scan_invalid():
    """Test that the html discovery plugin doesn't find non-html files."""
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    discovery_plugin = HTMLDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    assert not package["html_src"]


def test_html_discovery_plugin_scan_exceptions():
    """Test that the html discovery plugin properly respects exceptions."""
    discovery_plugin = HTMLDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    discovery_plugin.scan(package, "level", exceptions)
    expected_src = ["test.html"]
    if discovery_plugin.file_command_exists():
        expected_src += ["oddextensionhtml.source"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["html_src"]) == set(expected_src_fullpath)
