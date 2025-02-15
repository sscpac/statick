"""Unit tests for the YAMLLint tool plugin."""

import argparse
import os
import subprocess
import sys

import mock

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.yamllint import YamllintToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_yamllint_tool_plugin():
    """Construct and return an instance of the YAMLLint plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    yltp = YamllintToolPlugin()
    yltp.set_plugin_context(plugin_context)
    return yltp


def test_yamllint_tool_plugin_found():
    """Test that the plugin manager finds the YAMLLint plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "yamllint" for _, plugin in list(plugins.items())
    )


def test_yamllint_tool_plugin_scan_valid():
    """Integration test: Make sure the yamllint output hasn't changed."""
    yltp = setup_yamllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["yaml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "document-start.yaml")
    ]
    issues = yltp.scan(package, "level")
    if sys.platform == "win32":
        assert len(issues) == 2  # additional error about newline character
    else:
        assert len(issues) == 1


def test_yamllint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of yamllint."""
    yltp = setup_yamllint_tool_plugin()
    output = 'valid_package/document-start.yaml:1:1: [warning] missing document start "---" (document-start)'
    issues = yltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/document-start.yaml"
    assert issues[0].line_number == 1
    assert issues[0].tool == "yamllint"
    assert issues[0].issue_type == "document-start"
    assert issues[0].severity == 3
    assert issues[0].message == 'missing document start "---"'

    output = 'valid_package/document-start.yaml:1:1: [error] missing document start "---" (document-start)'
    issues = yltp.parse_output([output])
    assert issues[0].severity == 5


def test_yamllint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of yamllint."""
    yltp = setup_yamllint_tool_plugin()
    output = "invalid text"
    issues = yltp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.yamllint.subprocess.check_output")
def test_yamllint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means yamllint hit
    an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    yltp = setup_yamllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["yaml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "document-start.yaml")
    ]
    issues = yltp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = yltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.yamllint.subprocess.check_output")
def test_yamllint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means yamllint doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    yltp = setup_yamllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["yaml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "document-start.yaml")
    ]
    issues = yltp.scan(package, "level")
    assert issues is None
