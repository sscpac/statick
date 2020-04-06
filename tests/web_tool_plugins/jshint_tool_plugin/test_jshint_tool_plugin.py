"""Unit tests for the jshint plugin."""
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
from statick_tool.plugins.tool.jshint_tool_plugin import JSHintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_jshint_tool_plugin():
    """Initialize and return an instance of the jshint plugin."""
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
    plugin = JSHintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_jshint_tool_plugin_found():
    """Test that the plugin manager can find the jshint plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {"Tool": ToolPlugin,}
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "jshint"
    assert any(
        plugin_info.plugin_object.get_name() == "jshint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named jshint Tool Plugin
    assert any(
        plugin_info.name == "JSHint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_jshint_tool_plugin_scan_valid():
    """Integration test: Make sure the jshint output hasn't changed."""
    plugin = setup_jshint_tool_plugin()
    if not plugin.command_exists("jshint"):
        pytest.skip("Missing jshint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["javascript_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.js")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_jshint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the jshint output hasn't changed."""
    plugin = setup_jshint_tool_plugin()
    if not plugin.command_exists("jshint"):
        pytest.skip("Missing jshint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    package["javascript_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.js")
    ]
    issues = plugin.scan(package, "level")
    # We expect to have defined but not unsed errors.
    assert len(issues) == 2


def test_jshint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of jshint."""
    plugin = setup_jshint_tool_plugin()
    output = "test.html:8:11: 'log_out' is defined but never used."
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.html"
    assert issues[0].line_number == "8"
    assert issues[0].tool == "jshint"
    assert issues[0].issue_type == "jshint"
    assert issues[0].severity == 5
    assert issues[0].message == "'log_out' is defined but never used."


def test_jshint_tool_plugin_parse_invalid():
    """Verify that invalid output of jshint is ignored."""
    plugin = setup_jshint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.jshint_tool_plugin.subprocess.check_output")
def test_jshint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means jshint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_jshint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    package["javascript_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.js")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.jshint_tool_plugin.subprocess.check_output")
def test_jshint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means jshint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_jshint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    package["javascript_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.js")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
