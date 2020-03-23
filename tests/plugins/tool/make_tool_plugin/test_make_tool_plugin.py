"""Unit tests for the make tool plugin."""
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
from statick_tool.plugins.tool.make_tool_plugin import MakeToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_make_tool_plugin():
    """Construct and return an instance of the Make plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    mtp = MakeToolPlugin()
    mtp.set_plugin_context(plugin_context)
    return mtp


def test_make_tool_plugin_found():
    """Test that the plugin manager finds the Make plugin."""
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
    # Verify that a plugin's get_name() function returns "make"
    assert any(
        plugin_info.plugin_object.get_name() == "make"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Yamllint Tool Plugin
    assert any(
        plugin_info.name == "Make Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_make_tool_plugin_scan_valid():
    """Integration test: Make sure the make output hasn't changed."""
    mtp = setup_make_tool_plugin()
    if not mtp.command_exists("make"):
        pytest.skip("Missing make executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = "make_targets"
    issues = mtp.scan(package, "level")
    assert not issues


def test_make_tool_plugin_scan_missing_tool_name():
    """Check that a missing tool name results in an empty list of issues."""
    mtp = setup_make_tool_plugin()
    if not mtp.command_exists("make"):
        pytest.skip("Missing make executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = mtp.scan(package, "level")
    assert not issues


def test_make_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of make."""
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    output = "valid_package/hello.c:7:3: error: expected ; before return"
    issues = mtp.parse_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/hello.c"
    assert issues[0].line_number == "7"
    assert issues[0].severity == "5"
    assert issues[0].message == "expected ; before return"


def test_make_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of make."""
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    output = "invalid text"
    issues = mtp.parse_output(package, output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.make_tool_plugin.subprocess.check_output")
def test_make_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means make hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = "make_targets"
    issues = mtp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.make_tool_plugin.subprocess.check_output")
def test_make_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means make doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = "make_targets"
    issues = mtp.scan(package, "level")
    assert issues is None
