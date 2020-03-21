"""Unit tests for the lizard plugin."""
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
from statick_tool.plugins.tool.lizard_tool_plugin import LizardToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_lizard_tool_plugin():
    """Initialize and return an instance of the lizard plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    ltp = LizardToolPlugin()
    ltp.set_plugin_context(plugin_context)
    return ltp


def test_lizard_tool_plugin_found():
    """Test that the plugin manager can find the lizard plugin."""
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
    # Verify that a plugin's get_name() function returns "lizard"
    assert any(
        plugin_info.plugin_object.get_name() == "lizard"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Lizard Tool Plugin
    assert any(
        plugin_info.name == "Lizard Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_lizard_tool_plugin_scan_valid():
    """Integration test: Make sure the lizard output hasn't changed."""
    ltp = setup_lizard_tool_plugin()
    if not ltp.command_exists("lizard"):
        pytest.skip("Can't find lizard, unable to test lizard plugin")

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
    issues = ltp.scan(package, "level")
    assert len(issues) == 1
    assert issues[0].filename == os.path.join(
        os.path.dirname(__file__), "valid_package", "test.c"
    )
    assert issues[0].line_number == "2"
    assert issues[0].tool == "lizard"
    assert issues[0].issue_type == "warning"
    assert issues[0].severity == "5"
    assert (
        issues[0].message == "func has 52 NLOC, 16 CCN, 143 token, 0 PARAM, 69 length"
    )


def test_lizard_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of lizard."""
    ltp = setup_lizard_tool_plugin()
    output = "{}:1: warning: func has 22 NLOC, 18 CCN, 143 token, 0 PARAM, 69 length".format(
        os.path.join("valid_package", "test.c")
    )
    issues = ltp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == os.path.join("valid_package", "test.c")
    assert issues[0].line_number == "1"
    assert issues[0].tool == "lizard"
    assert issues[0].issue_type == "warning"
    assert issues[0].severity == "5"
    assert (
        issues[0].message == "func has 22 NLOC, 18 CCN, 143 token, 0 PARAM, 69 length"
    )


def test_lizard_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of lizard."""
    ltp = setup_lizard_tool_plugin()
    output = "invalid text"
    issues = ltp.parse_output(output)
    assert not issues


def test_lizard_tool_plugin_scan_missing_fields():
    """
    Test what happens when key fields are missing from the Package argument.

    Expected result: issues is empty
    """
    ltp = setup_lizard_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Missing src_dir
    issues = ltp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.lizard_tool_plugin.subprocess.check_output")
def test_lizard_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means lizard doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    ltp = setup_lizard_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
    issues = ltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.lizard_tool_plugin.subprocess.check_output")
def test_lizard_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means lizard hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    ltp = setup_lizard_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
    issues = ltp.scan(package, "level")
    assert issues is None
