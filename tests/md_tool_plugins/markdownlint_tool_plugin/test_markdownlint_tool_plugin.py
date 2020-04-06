"""Unit tests for the markdownlint plugin."""

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
from statick_tool.plugins.tool.markdownlint_tool_plugin import MarkdownlintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_markdownlint_tool_plugin():
    """Initialize and return an instance of the markdownlint plugin."""
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
    plugin = MarkdownlintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_markdownlint_tool_plugin_found():
    """Test that the plugin manager can find the markdownlint plugin."""
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
    # Verify that a plugin's get_name() function returns "markdownlint"
    assert any(
        plugin_info.plugin_object.get_name() == "markdownlint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named markdownlint Tool Plugin
    assert any(
        plugin_info.name == "Markdownlint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_markdownlint_tool_plugin_scan_valid():
    """Integration test: Make sure the markdownlint output hasn't changed."""
    plugin = setup_markdownlint_tool_plugin()
    if not plugin.command_exists("markdownlint"):
        pytest.skip("Missing markdownlint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.md")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_markdownlint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the markdownlint output hasn't changed."""
    plugin = setup_markdownlint_tool_plugin()
    if not plugin.command_exists("markdownlint"):
        pytest.skip("Missing markdownlint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    # We expect to have camelcase warnings and no-unused-var errors.
    assert len(issues) == 2


def test_markdownlint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of markdownlint."""
    plugin = setup_markdownlint_tool_plugin()
    output = "test.md:305 MD012/no-multiple-blanks Multiple consecutive blank lines [Expected: 1; Actual: 3]"
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.md"
    assert issues[0].line_number == "305"
    assert issues[0].tool == "markdownlint"
    assert issues[0].issue_type == "MD012/no-multiple-blanks"
    assert issues[0].severity == 3
    assert (
        issues[0].message == "Multiple consecutive blank lines [Expected: 1; Actual: 3]"
    )


def test_markdownlint_tool_plugin_parse_invalid():
    """Verify that invalid output of markdownlint is ignored."""
    plugin = setup_markdownlint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.markdownlint_tool_plugin.subprocess.check_output"
)
def test_markdownlint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means markdownlint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_markdownlint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.markdownlint_tool_plugin.subprocess.check_output"
)
def test_markdownlint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means markdownlint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_markdownlint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
