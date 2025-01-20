"""Unit tests for the rstcheck plugin."""
import argparse
import mock
import os
import pytest
import subprocess
import sys

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.rstcheck import RstcheckToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_rstcheck_tool_plugin():
    """Initialize and return an instance of the rstcheck plugin."""
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
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin = RstcheckToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_rstcheck_tool_plugin_found():
    """Test that the plugin manager can find the rstcheck plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "rstcheck" for _, plugin in list(plugins.items())
    )


def test_rstcheck_tool_plugin_scan_valid():
    """Integration test: Make sure the rstcheck output hasn't changed."""
    plugin = setup_rstcheck_tool_plugin()
    if not plugin.command_exists("rstcheck"):
        pytest.skip("Missing rstcheck executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.rst")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_rstcheck_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the rstcheck output hasn't changed."""
    plugin = setup_rstcheck_tool_plugin()
    if not plugin.command_exists("rstcheck"):
        pytest.skip("Missing rstcheck executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 1


def test_rstcheck_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of rstcheck."""
    plugin = setup_rstcheck_tool_plugin()
    output = "test.rst:305: (WARNING/2) Title underline too short."
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.rst"
    assert issues[0].line_number == "305"
    assert issues[0].tool == "rstcheck"
    assert issues[0].issue_type == "WARNING"
    assert issues[0].severity == "2"
    assert issues[0].message == "Title underline too short."


def test_rstcheck_tool_plugin_parse_invalid():
    """Verify that invalid output of rstcheck is ignored."""
    plugin = setup_rstcheck_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.rstcheck.subprocess.check_output")
def test_rstcheck_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means rstcheck hit an error).

    Expected result: no issues found
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_rstcheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.rstcheck.subprocess.check_output")
def test_rstcheck_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means rstcheck doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_rstcheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["rst_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.rst")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
