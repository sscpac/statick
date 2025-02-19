"""Unit tests for the markdownlint plugin."""
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
from statick_tool.plugins.tool.markdownlint import MarkdownlintToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_markdownlint_tool_plugin():
    """Initialize and return an instance of the markdownlint plugin."""
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
    plugin = MarkdownlintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_markdownlint_tool_plugin_found():
    """Test that the plugin manager can find the markdownlint plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "markdownlint" for _, plugin in list(plugins.items())
    )


def test_markdownlint_tool_plugin_scan_valid():
    """Integration test: Make sure the markdownlint output hasn't changed."""
    plugin = setup_markdownlint_tool_plugin()
    if not plugin.command_exists("markdownlint"):
        pytest.skip("Missing markdownlint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_no_issues.md")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_markdownlint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the markdownlint output hasn't changed."""
    plugin = setup_markdownlint_tool_plugin()
    if not plugin.command_exists("markdownlint"):
        pytest.skip("Missing markdownlint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 2


def test_markdownlint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of markdownlint."""
    plugin = setup_markdownlint_tool_plugin()
    output = "test.md:305:3 MD012/no-multiple-blanks Multiple consecutive blank lines [Expected: 1; Actual: 3]"
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.md"
    assert issues[0].line_number == 305
    assert issues[0].tool == "markdownlint"
    assert issues[0].issue_type == "MD012/no-multiple-blanks"
    assert issues[0].severity == 3
    assert (
        issues[0].message == "Multiple consecutive blank lines [Expected: 1; Actual: 3]"
    )


def test_markdownlint_tool_plugin_parse_invalid():
    """Verify that invalid output of markdownlint is ignored."""
    plugin = setup_markdownlint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.markdownlint.subprocess.check_output"
)
def test_markdownlint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means markdownlint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_markdownlint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.markdownlint.subprocess.check_output"
)
def test_markdownlint_tool_plugin_scan_nodejs_error(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised when nodejs throws an error.

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="internal/modules/cjs/loader.js:883 \
  throw err; \
  ^ \
\
Error: Cannot find module 'node:fs' \
Require stack:"
    )
    plugin = setup_markdownlint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="Require stack:"
    )
    issues = plugin.scan(package, "level")
    assert issues is None


@mock.patch(
    "statick_tool.plugins.tool.markdownlint.subprocess.check_output"
)
def test_markdownlint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means markdownlint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_markdownlint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["md_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.md")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
