"""Unit tests for the rstlint plugin."""
import argparse
import os
import pytest
import sys

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.rstlint import RstlintToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


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
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "rstlint" for _, plugin in list(plugins.items())
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
