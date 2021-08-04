"""Unit tests for the proselint plugin."""

import argparse
import json
import os

import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.proselint_tool_plugin import ProselintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_proselint_tool_plugin():
    """Initialize and return an instance of the proselint plugin."""
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
    plugin = ProselintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_proselint_tool_plugin_found():
    """Test that the plugin manager can find the proselint plugin."""
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
    # Verify that a plugin's get_name() function returns "proselint"
    assert any(
        plugin_info.plugin_object.get_name() == "proselint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named proselint Tool Plugin
    assert any(
        plugin_info.name == "Proselint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_proselint_tool_plugin_scan_valid():
    """Integration test: Make sure the proselint output hasn't changed."""
    plugin = setup_proselint_tool_plugin()
    if not plugin.command_exists("proselint"):
        pytest.skip("Missing proselint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.md")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_proselint_tool_plugin_scan_missing_src():
    """No issues should be found if no input files are provided."""
    plugin = setup_proselint_tool_plugin()
    if not plugin.command_exists("proselint"):
        pytest.skip("Missing proselint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = plugin.scan(package, "level")
    assert not issues


def test_proselint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the proselint output hasn't changed."""
    plugin = setup_proselint_tool_plugin()
    if not plugin.command_exists("proselint"):
        pytest.skip("Missing proselint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 2


def test_proselint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of proselint."""
    plugin = setup_proselint_tool_plugin()
    output = {}
    errors = {"data": {"errors": [{"check": "lexical_illusions.misc", "column": 48, "end": 5231, "extent": 12, "line": 154, "message": "There's a lexical illusion here: a word is repeated.", "replacements": None, "severity": "warning", "start": 5219}]}, "status": "success"}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == "test.md"
    assert issues[0].line_number == "154"
    assert issues[0].tool == "proselint"
    assert issues[0].issue_type == "lexical_illusions.misc"
    assert issues[0].severity == "3"
    assert issues[0].message == "There's a lexical illusion here: a word is repeated."

    errors = {"data": {"errors": []}, "status": "success"}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert not issues

    errors = {"data": {"errors": [{"severity": "suggestion", "check": None, "line": None, "message": None}]}, "status": "success"}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert len(issues) == 1
    assert issues[0].severity == "1"

    errors = {"data": {"errors": [{"severity": "error", "check": None, "line": None, "message": None}]}, "status": "success"}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert len(issues) == 1
    assert issues[0].severity == "5"

    errors = {"data": {"errors": [{"severity": "not_a_valid_severity", "check": None, "line": None, "message": None}]}, "status": "success"}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert len(issues) == 1
    assert issues[0].severity == "3"


def test_proselint_tool_plugin_parse_invalid():
    """Verify that invalid output of proselint is ignored."""
    plugin = setup_proselint_tool_plugin()
    output = {}
    errors = {}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert not issues

    errors = {"data": {"errors": [{}]}, "status": "success"}
    output["test.md"] = json.dumps(errors)
    issues = plugin.parse_output(output)
    assert not issues
