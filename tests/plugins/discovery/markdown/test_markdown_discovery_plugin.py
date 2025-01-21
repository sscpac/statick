"""Unit tests for the markdown discovery plugin."""
import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.markdown import MarkdownDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_markdown_plugin_found():
    """Test that the plugin manager finds the markdown discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "markdown" for _, plugin in list(discovery_plugins.items())
    )


def test_markdown_plugin_scan_valid():
    """Test that the markdown discovery plugin finds valid markdown source and bib files."""
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    discovery_plugin = MarkdownDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    expected = ["test.md", os.path.join("ignore_this", "ignoreme.md")]
    # if discovery_plugin.file_command_exists():
    #     expected += ['oddextensionmarkdown.source']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["md_src"]) == set(expected_fullpath)


def test_markdown_plugin_scan_invalid():
    """Test that the markdown discovery plugin doesn't find non-markdown files."""
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    discovery_plugin = MarkdownDiscoveryPlugin()
    discovery_plugin.scan(package, "level")
    assert not package["md_src"]


def test_markdown_discovery_plugin_scan_exceptions():
    """Test that the markdown discovery plugin properly respects exceptions."""
    discovery_plugin = MarkdownDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    discovery_plugin.scan(package, "level", exceptions)
    expected_src = ["test.md"]
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [
        os.path.join(package.path, filename) for filename in expected_src
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["md_src"]) == set(expected_src_fullpath)
