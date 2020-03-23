"""xmllint unit tests."""
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
from statick_tool.plugins.tool.xmllint_tool_plugin import XmllintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_xmllint_tool_plugin():
    """Create an instance of the xmllint plugin."""
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
    xltp = XmllintToolPlugin()
    xltp.set_plugin_context(plugin_context)
    return xltp


def test_xmllint_tool_plugin_found():
    """Test that the plugin manager finds the xmllint plugin."""
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
    # Verify that a plugin's get_name() function returns "xmllint"
    assert any(
        plugin_info.plugin_object.get_name() == "xmllint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Xmllint Tool Plugin
    assert any(
        plugin_info.name == "xmllint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_xmllint_tool_plugin_scan_valid():
    """Integration test: Make sure the xmllint output hasn't changed."""
    xltp = setup_xmllint_tool_plugin()
    if not xltp.command_exists("xmllint"):
        pytest.skip("Missing xmllint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["xml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "premature_end.xml")
    ]
    issues = xltp.scan(package, "level")
    assert len(issues) == 2


def test_xmllint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of xmllint."""
    xltp = setup_xmllint_tool_plugin()
    output = "valid_package/premature_end.xml:3: parser error : Opening and ending tag mismatch: notclosed line 2 and tag"
    issues = xltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/premature_end.xml"
    assert issues[0].line_number == "3"
    assert issues[0].tool == "xmllint"
    assert issues[0].issue_type == "parser error"
    assert issues[0].severity == "5"
    assert (
        issues[0].message == "Opening and ending tag mismatch: notclosed line 2 and tag"
    )


def test_xmllint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of xmllint."""
    xltp = setup_xmllint_tool_plugin()
    output = "invalid text"
    issues = xltp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.xmllint_tool_plugin.subprocess.check_output")
def test_xmllint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means xmllint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    xltp = setup_xmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["xml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "premature_end.xml")
    ]
    issues = xltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.xmllint_tool_plugin.subprocess.check_output")
def test_xmllint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means xmllint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    xltp = setup_xmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["xml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "premature_end.xml")
    ]
    issues = xltp.scan(package, "level")
    assert issues is None
