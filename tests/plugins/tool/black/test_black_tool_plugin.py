"""Unit tests for the black plugin."""

import argparse
import os
import subprocess
import sys

import mock
import pytest

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.black import BlackToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_black_tool_plugin():
    """Create and return an instance of the PyCodeStyle plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    btp = BlackToolPlugin()
    btp.set_plugin_context(plugin_context)
    return btp


def test_black_tool_plugin_found():
    """Test that the plugin manager can find the PyCodeStyle plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "black" for _, plugin in list(plugins.items())
    )


def test_black_tool_plugin_scan_valid():
    """Integration test: Make sure the black output hasn't changed."""
    btp = setup_black_tool_plugin()
    if not btp.command_exists("black"):
        pytest.skip("Can't find black, unable to test black plugin.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "format_errors.py")
    ]
    issues = btp.scan(package, "level")
    assert len(issues) == 1


def test_black_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of black."""
    btp = setup_black_tool_plugin()
    output = "would reformat /home/user/valid_package/format_errors.py"
    issues = btp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/format_errors.py"
    assert issues[0].line_number == 0
    assert issues[0].tool == "black"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 3
    assert issues[0].message == "would reformat"

    output = "error: cannot format /home/user/file: INTERNAL ERROR: message: /tmp/x"
    issues = btp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/file"
    assert issues[0].line_number == 0
    assert issues[0].tool == "black"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 3
    assert issues[0].message == "message"

    output = "error: cannot format /home/user/file: Cannot parse: 1:3: {faulty line}"
    issues = btp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/file"
    assert issues[0].line_number == 1
    assert issues[0].tool == "black"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 3
    assert issues[0].message == "Cannot parse {faulty line}"


def test_black_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of black."""
    btp = setup_black_tool_plugin()
    output = "invalid text"
    issues = btp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.black.subprocess.check_output")
def test_black_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means black doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    btp = setup_black_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "format_errors.py")
    ]
    issues = btp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.black.subprocess.check_output")
def test_black_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means black hit an
    error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    btp = setup_black_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "format_errors.py")
    ]
    issues = btp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.black.subprocess.check_output")
def test_black_tool_plugin_scan_internal_error(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised due to an internal error.

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        123, "", output="error: cannot format /tmp/x: INTERNAL ERROR: message: /tmp/x"
    )
    btp = setup_black_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "format_errors.py")
    ]
    issues = btp.scan(package, "level")
    assert len(issues) == 1
