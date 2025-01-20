"""Unit tests for the perlcritic plugin."""

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
from statick_tool.plugins.tool.perlcritic import PerlCriticToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_perlcritic_tool_plugin(binary=None):
    """Initialize and return a perlcritic plugin."""
    arg_parser = argparse.ArgumentParser()
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
    if binary:
        plugin_context.args.perlcritic_bin = binary
    pctp.set_plugin_context(plugin_context)
    return pctp


def test_perlcritic_tool_plugin_found():
    """Test that the plugin manager can find the perlcritic plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "perlcritic" for _, plugin in list(plugins.items())
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


def test_perlcritic_tool_plugin_scan_wrong_binary():
    """Verify that no issues are found when using the wrong binary."""
    pctp = setup_perlcritic_tool_plugin(binary="wrong-binary")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    package["perl_src"] = []
    package["perl_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.pl")
    ]
    issues = pctp.scan(package, "level")
    assert not issues


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


def test_perlcritic_tool_plugin_parse_warnings_mapping():
    """Verify that we can use a mapping to find the SEI Cert reference from a
    warning."""
    pctp = setup_perlcritic_tool_plugin()
    output = (
        "valid_package/test.pl:::2:::InputOutput::ProhibitTwoArgOpen:::any string:::5"
    )
    issues = pctp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/test.pl"
    assert issues[0].line_number == "2"
    assert issues[0].tool == "perlcritic"
    assert issues[0].issue_type == "InputOutput::ProhibitTwoArgOpen"
    assert issues[0].severity == "5"
    assert issues[0].message == "any string"
    assert issues[0].cert_reference == "IDS31-PL"


def test_perlcritic_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of perlcritic."""
    pctp = setup_perlcritic_tool_plugin()
    output = "invalid text"
    issues = pctp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.perlcritic.subprocess.check_output")
def test_perlcritic_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means perlcritic doesn't
    exist).

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


@mock.patch("statick_tool.plugins.tool.perlcritic.subprocess.check_output")
def test_perlcritic_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means perlcritic
    hit an error).

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
