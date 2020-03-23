"""Unit tests for the perlcritic plugin."""
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
from statick_tool.plugins.tool.perlcritic_tool_plugin import PerlCriticToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_perlcritic_tool_plugin():
    """Initialize and return a perlcritic plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--perlcritic-bin", dest="perlcritic_bin")
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    pctp = PerlCriticToolPlugin()
    pctp.set_plugin_context(plugin_context)
    return pctp


def test_perlcritic_tool_plugin_found():
    """Test that the plugin manager can find the perlcritic plugin."""
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
    # Verify that a plugin's get_name() function returns "perlcritic"
    assert any(
        plugin_info.plugin_object.get_name() == "perlcritic"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named PerlCritic Tool Plugin
    assert any(
        plugin_info.name == "Perl::Critic Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_perlcritic_tool_plugin_scan_valid():
    """Integration test: Make sure the perlcritic output hasn't changed."""
    pctp = setup_perlcritic_tool_plugin()
    if not pctp.command_exists("perlcritic"):
        pytest.skip("perlcritic command not available, can't test its output")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    # Do not include perl_src
    issues = pctp.scan(package, "level")
    assert not issues

    # Pass in empty perl_src
    package["perl_src"] = []
    issues = pctp.scan(package, "level")
    assert not issues

    package["perl_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.pl")
    ]
    issues = pctp.scan(package, "level")
    assert len(issues) == 1
    assert issues[0].line_number == "2"
    assert issues[0].tool == "perlcritic"
    assert issues[0].issue_type == "InputOutput::ProhibitBarewordFileHandles"
    assert issues[0].severity == "5"
    assert issues[0].message == "Bareword file handle opened"


def test_perlcritic_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of perlcritic."""
    pctp = setup_perlcritic_tool_plugin()
    output = "valid_package/test.pl:::2:::InputOutput::ProhibitBarewordFileHandles:::Bareword file handle opened:::5"
    issues = pctp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/test.pl"
    assert issues[0].line_number == "2"
    assert issues[0].tool == "perlcritic"
    assert issues[0].issue_type == "InputOutput::ProhibitBarewordFileHandles"
    assert issues[0].severity == "5"
    assert issues[0].message == "Bareword file handle opened"


def test_perlcritic_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of perlcritic."""
    pctp = setup_perlcritic_tool_plugin()
    output = "invalid text"
    issues = pctp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.perlcritic_tool_plugin.subprocess.check_output")
def test_perlcritic_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means perlcritic doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    pctp = setup_perlcritic_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["perl_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.pl")
    ]
    issues = pctp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.perlcritic_tool_plugin.subprocess.check_output")
def test_perlcritic_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means perlcritic hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    pctp = setup_perlcritic_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["perl_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.pl")
    ]
    issues = pctp.scan(package, "level")
    assert not issues
