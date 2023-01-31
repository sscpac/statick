"""Unit tests for the ruff plugin."""
import argparse
import os
import subprocess

import mock
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.ruff_tool_plugin import RuffToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_ruff_tool_plugin():
    """Initialize and return a ruff plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    rtp = RuffToolPlugin()
    rtp.set_plugin_context(plugin_context)
    return rtp


def test_ruff_tool_plugin_found():
    """Test that the plugin manager can find the ruff plugin."""
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
    # Verify that a plugin's get_name() function returns "ruff"
    assert any(
        plugin_info.plugin_object.get_name() == "ruff"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named ruff Tool Plugin
    assert any(
        plugin_info.name == "Ruff Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_ruff_tool_plugin_scan_valid():
    """Integration test: Make sure the ruff output hasn't changed."""
    rtp = setup_ruff_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "ruff_test.py")
    ]
    issues = rtp.scan(package, "level")
    assert len(issues) == 1


def test_ruff_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of ruff."""
    rtp = setup_ruff_tool_plugin()
    output = "some_file.py:644:89: E501 Line too long (96 > 88 characters)"
    issues = rtp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "some_file.py"
    assert issues[0].line_number == "644"
    assert issues[0].tool == "ruff"
    assert issues[0].issue_type == "E501"
    assert issues[0].severity == "5"
    assert issues[0].message == "Line too long (96 > 88 characters)"

    output = "a_file.py:21:1: E402 Module level import not at top of file"
    issues = rtp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "a_file.py"
    assert issues[0].line_number == "21"
    assert issues[0].tool == "ruff"
    assert issues[0].issue_type == "E402"
    assert issues[0].severity == "5"
    assert issues[0].message == "Module level import not at top of file"


def test_ruff_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of ruff."""
    rtp = setup_ruff_tool_plugin()
    output = "invalid text"
    issues = rtp.parse_output([output])
    assert not issues


@mock.patch("statick_tool.plugins.tool.ruff_tool_plugin.subprocess.check_output")
def test_ruff_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means ruff hit an
    error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    rtp = setup_ruff_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "ruff_test.py")
    ]
    issues = rtp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = rtp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.ruff_tool_plugin.subprocess.check_output")
def test_ruff_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means ruff doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    rtp = setup_ruff_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "ruff_test.py")
    ]
    issues = rtp.scan(package, "level")
    assert issues is None
