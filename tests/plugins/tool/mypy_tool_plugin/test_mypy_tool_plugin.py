"""Unit tests for the mypy plugin."""
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
from statick_tool.plugins.tool.mypy_tool_plugin import MypyToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_mypy_tool_plugin():
    """Create and return an instance of the Mypy plugin."""
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
    mtp = MypyToolPlugin()
    mtp.set_plugin_context(plugin_context)
    return mtp


def test_mypy_tool_plugin_found():
    """Test that the plugin manager can find the Mypy plugin."""
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
    # Verify that a plugin's get_name() function returns "mypy"
    assert any(
        plugin_info.plugin_object.get_name() == "mypy"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Mypy Tool Plugin
    assert any(
        plugin_info.name == "Mypy Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_mypy_tool_plugin_scan_valid():
    """Integration test: Make sure the mypy output hasn't changed."""
    mtp = setup_mypy_tool_plugin()
    if not mtp.command_exists("mypy"):
        pytest.skip("Can't find mypy, unable to test mypy plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "wrong_mypy.py")
    ]
    issues = mtp.scan(package, "level")
    assert len(issues) == 1


def test_mypy_tool_plugin_scan_invalid():
    """Make sure no issues are found when no Python source files are available."""
    mtp = setup_mypy_tool_plugin()
    if not mtp.command_exists("mypy"):
        pytest.skip("Can't find mypy, unable to test mypy plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = mtp.scan(package, "level")
    assert not issues


def test_mypy_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of mypy."""
    mtp = setup_mypy_tool_plugin()
    output = "/home/user/valid_package/wrong_mypy.py:1: error: Incompatible types in assignment (expression has type str, variable has type int) [assignment]"
    issues = mtp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/wrong_mypy.py"
    assert issues[0].line_number == "1"
    assert issues[0].tool == "mypy"
    assert issues[0].issue_type == "assignment"
    assert issues[0].severity == "5"
    assert (
        issues[0].message
        == "Incompatible types in assignment (expression has type str, variable has type int)"
    )


def test_mypy_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of mypy."""
    mtp = setup_mypy_tool_plugin()
    output = "invalid text"
    issues = mtp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.mypy_tool_plugin.subprocess.check_output")
def test_mypy_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means mypy doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    mtp = setup_mypy_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "wrong_mypy.py")
    ]
    issues = mtp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.mypy_tool_plugin.subprocess.check_output")
def test_mypy_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means mypy hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    mtp = setup_mypy_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "wrong_mypy.py")
    ]
    issues = mtp.scan(package, "level")
    assert not issues
