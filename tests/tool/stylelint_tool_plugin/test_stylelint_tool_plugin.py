"""Unit tests for the stylelint plugin."""
import argparse
import os
import subprocess

import mock
import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.stylelint_tool_plugin import StylelintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_stylelint_tool_plugin():
    """Initialize and return an instance of the stylelint plugin."""
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
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin = StylelintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_stylelint_tool_plugin_found():
    """Test that the plugin manager can find the stylelint plugin."""
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
    # Verify that a plugin's get_name() function returns "stylelint"
    assert any(
        plugin_info.plugin_object.get_name() == "stylelint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named stylelint Tool Plugin
    assert any(
        plugin_info.name == "stylelint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_stylelint_tool_plugin_scan_valid():
    """Integration test: Make sure the stylelint output hasn't changed."""
    plugin = setup_stylelint_tool_plugin()
    if not plugin.command_exists("stylelint"):
        pytest.skip("Missing stylelint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["css_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.css")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_stylelint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the stylelint output hasn't changed."""
    plugin = setup_stylelint_tool_plugin()
    if not plugin.command_exists("stylelint"):
        pytest.skip("Missing stylelint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    package["css_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.css")
    ]
    issues = plugin.scan(package, "level")
    # We expect to have declaration-colon-after-space and block-opening-brace-space-before errors.
    assert len(issues) == 3


def test_stylelint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of stylelint."""
    plugin = setup_stylelint_tool_plugin()
    output = '[{"source":"test.css","deprecations":[],"invalidOptionWarnings":[],"parseErrors":[],"errored":true,"warnings":[{"line":3,"column":13,"rule":"declaration-block-trailing-semicolon","severity":"error","text":"Expected a trailing semicolon (declaration-block-trailing-semicolon)"}]}]'
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.css"
    assert issues[0].line_number == 3
    assert issues[0].tool == "stylelint"
    assert issues[0].issue_type == "declaration-block-trailing-semicolon"
    assert issues[0].severity == 5
    assert (
        issues[0].message
        == "Expected a trailing semicolon (declaration-block-trailing-semicolon)"
    )


def test_stylelint_tool_plugin_parse_invalid():
    """Verify that invalid output of stylelint is ignored."""
    plugin = setup_stylelint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.stylelint_tool_plugin.subprocess.check_output")
def test_stylelint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means stylelint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_stylelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    package["css_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.css")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.stylelint_tool_plugin.subprocess.check_output")
def test_stylelint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means stylelint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_stylelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    package["css_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.css")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
