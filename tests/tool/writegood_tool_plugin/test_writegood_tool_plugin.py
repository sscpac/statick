"""Unit tests for the writegood plugin."""

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
from statick_tool.plugins.tool.writegood_tool_plugin import WriteGoodToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_writegood_tool_plugin():
    """Initialize and return an instance of the writegood plugin."""
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
    plugin = WriteGoodToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_writegood_tool_plugin_found():
    """Test that the plugin manager can find the writegood plugin."""
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
    # Verify that a plugin's get_name() function returns "writegood"
    assert any(
        plugin_info.plugin_object.get_name() == "writegood"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named writegood Tool Plugin
    assert any(
        plugin_info.name == "WriteGood Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_writegood_tool_plugin_scan_valid():
    """Integration test: Make sure the writegood output hasn't changed."""
    plugin = setup_writegood_tool_plugin()
    if not plugin.command_exists("writegood"):
        pytest.skip("Missing writegood executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.md")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_writegood_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the writegood output hasn't changed."""
    plugin = setup_writegood_tool_plugin()
    if not plugin.command_exists("writegood"):
        pytest.skip("Missing writegood executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md"),
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 3
    assert issues[0].filename == os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    assert issues[0].line_number == "4"
    assert issues[0].tool == "writegood"
    assert issues[0].issue_type == "suggestion"
    assert issues[0].severity == "1"
    assert issues[0].message == "\"So\" adds no meaning"
    assert issues[1].filename == os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    assert issues[1].line_number == "4"
    assert issues[1].tool == "writegood"
    assert issues[1].issue_type == "suggestion"
    assert issues[1].severity == "1"
    assert issues[1].message == "\"was stolen\" may be passive voice"
    assert issues[2].filename == os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    assert issues[2].line_number == "6"
    assert issues[2].tool == "writegood"
    assert issues[2].issue_type == "suggestion"
    assert issues[2].severity == "1"
    assert issues[2].message == "\"only\" can weaken meaning"


def test_writegood_tool_plugin_scan_valid_with_issues_rst():
    """Integration test: Make sure the writegood output hasn't changed."""
    plugin = setup_writegood_tool_plugin()
    if not plugin.command_exists("writegood"):
        pytest.skip("Missing writegood executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.rst"),
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 3
    assert issues[0].filename == os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    assert issues[0].line_number == "4"
    assert issues[0].tool == "writegood"
    assert issues[0].issue_type == "suggestion"
    assert issues[0].severity == "1"
    assert issues[0].message == "\"So\" adds no meaning"
    assert issues[1].filename == os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    assert issues[1].line_number == "4"
    assert issues[1].tool == "writegood"
    assert issues[1].issue_type == "suggestion"
    assert issues[1].severity == "1"
    assert issues[1].message == "\"was stolen\" may be passive voice"
    assert issues[2].filename == os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    assert issues[2].line_number == "6"
    assert issues[2].tool == "writegood"
    assert issues[2].issue_type == "suggestion"
    assert issues[2].severity == "1"
    assert issues[2].message == "\"only\" can weaken meaning"


def test_writegood_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of writegood."""
    plugin = setup_writegood_tool_plugin()
    output = "README.md:16:22:be applied may be passive voice"
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "README.md"
    assert issues[0].line_number == "16"
    assert issues[0].tool == "writegood"
    assert issues[0].issue_type == "suggestion"
    assert issues[0].severity == "1"
    assert (
        issues[0].message == "be applied may be passive voice"
    )


def test_writegood_tool_plugin_parse_invalid():
    """Verify that invalid output of writegood is ignored."""
    plugin = setup_writegood_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.writegood_tool_plugin.subprocess.check_output"
)
def test_writegood_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means writegood hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        33, "", output="mocked error"
    )
    plugin = setup_writegood_tool_plugin()
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

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        255, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.writegood_tool_plugin.subprocess.check_output"
)
def test_writegood_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means writegood doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_writegood_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
