"""Unit tests for the lacheck plugin."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import mock
import pytest
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources

import statick_tool
from statick_tool.plugins.tool.lacheck import LacheckToolPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_lacheck_tool_plugin():
    """Initialize and return an instance of the lacheck plugin."""
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
    ltp = LacheckToolPlugin()
    ltp.set_plugin_context(plugin_context)
    return ltp


def test_lacheck_tool_plugin_found():
    """Test that the plugin manager can find the lacheck plugin."""
    tool_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        tool_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "lacheck" for _, plugin in list(tool_plugins.items())
    )


def test_lacheck_tool_plugin_scan_valid():
    """Integration test: Make sure the lacheck output hasn't changed."""
    ltp = setup_lacheck_tool_plugin()
    if not ltp.command_exists("lacheck"):
        pytest.skip("Missing lacheck executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["tex"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.tex")
    ]
    issues = ltp.scan(package, "level")
    # We expect to have space before punctuation mark warning.
    assert len(issues) == 1

    try:
        os.remove(os.path.join(os.getcwd(), "lacheck.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


def test_lacheck_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of lacheck."""
    ltp = setup_lacheck_tool_plugin()
    # Note that misspelled punctation matches actual tool output.
    output = (
        "'valid_package/test.tex', line 13: Whitespace before punctation mark in ' .'"
    )
    issues = ltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/test.tex"
    assert issues[0].line_number == 13
    assert issues[0].tool == "lacheck"
    assert issues[0].issue_type == "lacheck"
    assert issues[0].severity == 3
    assert issues[0].message == "Whitespace before punctation mark in ' .'"


def test_lacheck_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of lacheck."""
    ltp = setup_lacheck_tool_plugin()
    output = "invalid text"
    issues = ltp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.lacheck.subprocess.check_output")
def test_lacheck_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means lacheck hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    ltp = setup_lacheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["tex"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.tex")
    ]
    issues = ltp.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    issues = ltp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.lacheck.subprocess.check_output")
def test_lacheck_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means lacheck doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    ltp = setup_lacheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["tex"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.tex")
    ]
    issues = ltp.scan(package, "level")
    assert issues is None

    log_file = Path("lacheck.log")
    if log_file.is_file():
        try:
            log_file.unlink()
        except FileNotFoundError as ex:
            print(f"Error: {ex}")
        except OSError as ex:
            print(f"Error: {ex}")
