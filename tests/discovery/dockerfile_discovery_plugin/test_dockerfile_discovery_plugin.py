"""Unit tests for the dockerfile discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.dockerfile_discovery_plugin import (
    DockerfileDiscoveryPlugin,
)


def test_dockerfile_plugin_found():
    """Test that the plugin manager finds the dockerfile discovery plugin."""
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
    # Verify that a plugin's get_name() function returns "dockerfile"
    assert any(
        plugin_info.plugin_object.get_name() == "dockerfile"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named dockerfile Discovery Plugin
    assert any(
        plugin_info.name == "Dockerfile Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_dockerfile_plugin_scan_valid():
    """Test that the dockerfile discovery plugin finds valid dockerfile source and bib files."""
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    discovery_plugin = DockerfileDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    expected = ["Dockerfile", os.path.join("ignore_this", "Dockerfile.ignoreme")]
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["dockerfile_src"]) == set(expected_fullpath)


def test_dockerfile_plugin_scan_invalid():
    """Test that the dockerfile discovery plugin doesn't find non-dockerfile files."""
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    discovery_plugin = DockerfileDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    assert not package["dockerfile_src"]


def test_dockerfile_discovery_plugin_scan_exceptions():
    """Test that the dockerfile discovery plugin properly respects exceptions."""
    discovery_plugin = DockerfileDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    discovery_plugin.scan(package, "level", exceptions)
    expected_src = ["Dockerfile"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["dockerfile_src"]) == set(expected_src_fullpath)
