"""Unit tests for the chktex plugin."""
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
from statick_tool.plugins.tool.chktex import ChktexToolPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_chktex_tool_plugin():
    """Initialize and return an instance of the chktex plugin."""
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
    ctp = ChktexToolPlugin()
    ctp.set_plugin_context(plugin_context)
    return ctp


def test_chktex_tool_plugin_found():
    """Test that the plugin manager can find the chktex plugin."""
    tool_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        tool_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "chktex" for _, plugin in list(tool_plugins.items())
    )


def test_chktex_tool_plugin_scan_valid():
    """Integration test: Make sure the chktex output hasn't changed."""
    cttp = setup_chktex_tool_plugin()
    if not cttp.command_exists("chktex"):
        pytest.skip("Missing chktex executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["tex"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.tex")
    ]
    issues = cttp.scan(package, "level")
    # We expect to have length of dash warning.
    assert len(issues) == 1

    try:
        os.remove(os.path.join(os.getcwd(), "chktex.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


def test_chktex_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of chktex."""
    cttp = setup_chktex_tool_plugin()
    output = (
        "a\nb\nc\nd\nWarning 8 in /e line 13: Wrong length of dash may have been used.\n"
        "Adding intentional chktex warning -- for dashes --- should have three of them.\n^^\n"
    )
    issues = cttp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].line_number == 13
    assert issues[0].tool == "chktex"
    assert issues[0].issue_type == "8"
    assert issues[0].severity == 3
    assert issues[0].message == "Wrong length of dash may have been used."


def test_chktex_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of chktex."""
    cttp = setup_chktex_tool_plugin()
    output = "invalid text"
    issues = cttp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.chktex.subprocess.check_output")
def test_chktex_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means chktex hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    cttp = setup_chktex_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["tex"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.tex")
    ]
    issues = cttp.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    issues = cttp.scan(package, "level")
    assert not issues

    try:
        os.remove(os.path.join(os.getcwd(), "chktex.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


@mock.patch("statick_tool.plugins.tool.chktex.subprocess.check_output")
def test_chktex_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means chktex doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cttp = setup_chktex_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["tex"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.tex")
    ]
    issues = cttp.scan(package, "level")
    assert issues is None

    log_file = Path("chktex.log")
    if log_file.is_file():
        try:
            log_file.unlink()
        except FileNotFoundError as ex:
            print(f"Error: {ex}")
        except OSError as ex:
            print(f"Error: {ex}")
