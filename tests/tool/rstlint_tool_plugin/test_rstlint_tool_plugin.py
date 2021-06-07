"""Unit tests for the rstlint plugin."""

import argparse
import os

import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.rstlint_tool_plugin import RstlintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_rstlint_tool_plugin():
    """Initialize and return an instance of the rstlint plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )

    resources = Resources(
        [
            os.path.join(os.path.dirname(statick_tool.__file__), "plugins"),
            os.path.join(os.path.dirname(__file__), "valid_package"),
        ]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin = RstlintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_rstlint_tool_plugin_found():
    """Test that the plugin manager can find the rstlint plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {
            "Tool": ToolPlugin,
        }
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "rstlint"
    assert any(
        plugin_info.plugin_object.get_name() == "rstlint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named rstlint Tool Plugin
    assert any(
        plugin_info.name == "rstlint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_rstlint_tool_plugin_scan_valid():
    """Integration test: Make sure the rstlint output hasn't changed."""
    plugin = setup_rstlint_tool_plugin()
    if not plugin.command_exists("rst-lint"):
        pytest.skip("Missing rstlint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.rst")
    ]
    print(package)
    issues = plugin.scan(package, "level")
    assert not issues


def test_rstlint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the rstlint output hasn't changed."""
    plugin = setup_rstlint_tool_plugin()
    if not plugin.command_exists("rst-lint"):
        pytest.skip("Missing rstlint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 1
