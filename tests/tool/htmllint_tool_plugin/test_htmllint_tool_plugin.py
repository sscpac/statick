"""Unit tests for the htmllint plugin."""

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
from statick_tool.plugins.tool.htmllint_tool_plugin import HTMLLintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_htmllint_tool_plugin():
    """Initialize and return an instance of the htmllint plugin."""
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
    plugin = HTMLLintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_htmllint_tool_plugin_found():
    """Test that the plugin manager can find the htmllint plugin."""
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
    # Verify that a plugin's get_name() function returns "htmllint"
    assert any(
        plugin_info.plugin_object.get_name() == "htmllint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named htmllint Tool Plugin
    assert any(
        plugin_info.name == "HTMLLint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_htmllint_tool_plugin_scan_valid():
    """Integration test: Make sure the htmllint output hasn't changed."""
    plugin = setup_htmllint_tool_plugin()
    if not plugin.command_exists("htmllint"):
        pytest.skip("Missing htmllint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.html")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_htmllint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the htmllint output hasn't changed."""
    plugin = setup_htmllint_tool_plugin()
    if not plugin.command_exists("htmllint"):
        pytest.skip("Missing htmllint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    issues = plugin.scan(package, "level")
    # We expect to have tag not closed warning.
    assert len(issues) == 1


def test_htmllint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of htmllint."""
    plugin = setup_htmllint_tool_plugin()
    output = "test.html: line 12, col 3, tag is not closed"
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.html"
    assert issues[0].line_number == "12"
    assert issues[0].tool == "htmllint"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 3
    assert issues[0].message == "tag is not closed"


def test_htmllint_tool_plugin_parse_invalid():
    """Verify that invalid output of htmllint is ignored."""
    plugin = setup_htmllint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.htmllint_tool_plugin.subprocess.check_output")
def test_htmllint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means htmllint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_htmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.htmllint_tool_plugin.subprocess.check_output")
def test_htmllint_tool_plugin_scan_nodejs_error(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised when nodejs throws an error.

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1,
        "",
        output="internal/modules/cjs/loader.js:883 \
  throw err; \
  ^ \
\
Error: Cannot find module 'node:fs' \
Require stack:",
    )
    plugin = setup_htmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="Require stack:"
    )
    issues = plugin.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.htmllint_tool_plugin.subprocess.check_output")
def test_htmllint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means htmllint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_htmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["html_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.html")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
