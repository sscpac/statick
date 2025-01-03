"""Unit tests for the flawfinder plugin."""

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
from statick_tool.plugins.tool.flawfinder import FlawfinderToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_flawfinder_tool_plugin():
    """Initialize and return an instance of the flawfinder plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--flawfinder-bin", dest="flawfinder_bin")
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    fftp = FlawfinderToolPlugin()
    fftp.set_plugin_context(plugin_context)
    return fftp


def test_flawfinder_tool_plugin_found():
    """Test that the plugin manager can find the flawfinder plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "flawfinder" for _, plugin in list(plugins.items())
    )


def test_flawfinder_tool_plugin_scan_valid():
    """Integration test: Make sure the flawfinder output hasn't changed."""
    fftp = setup_flawfinder_tool_plugin()
    if not fftp.command_exists("flawfinder"):
        pytest.skip("Flawfinder binary not found, can't run the integration test")
    if sys.platform == "win32":
        pytest.skip("Flawfinder needs Cygwin on Windows, skipping test.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [os.path.join(package.path, "strlen.c")]
    issues = fftp.scan(package, "level")
    assert len(issues) == 1


def test_flawfinder_tool_plugin_scan_missing_c_src():
    """Check what happens if the plugin isn't passed any source files."""
    fftp = setup_flawfinder_tool_plugin()
    if not fftp.command_exists("flawfinder"):
        pytest.skip("Flawfinder binary not found, can't run the integration test")
    if sys.platform == "win32":
        pytest.skip("Flawfinder needs Cygwin on Windows, skipping test.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = fftp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.flawfinder.subprocess.check_output")
def test_flawfinder_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means flawfinder doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    fftp = setup_flawfinder_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [os.path.join(package.path, "strlen.c")]
    issues = fftp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.flawfinder.subprocess.check_output")
def test_flawfinder_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means flawfinder
    hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    fftp = setup_flawfinder_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [os.path.join(package.path, "strlen.c")]
    issues = fftp.scan(package, "level")
    assert issues is None


def test_flawfinder_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of flawfinder."""
    fftp = setup_flawfinder_tool_plugin()
    output = "strlen.c:2:  [1] (buffer) strlen:Does not handle strings that are not \0-terminated; if given one it may perform an over-read (it could cause a crash if unprotected) (CWE-126)."
    issues = fftp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "strlen.c"
    assert issues[0].line_number == "2"
    assert issues[0].tool == "flawfinder"
    assert issues[0].issue_type == "(buffer) strlen"
    assert issues[0].severity == "1"
    assert (
        issues[0].message
        == "Does not handle strings that are not \0-terminated; if given one it may perform an over-read (it could cause a crash if unprotected) (CWE-126)."
    )


def test_flawfinder_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of flawfinder."""
    fftp = setup_flawfinder_tool_plugin()
    output = "invalid text"
    issues = fftp.parse_output(output)
    assert not issues
