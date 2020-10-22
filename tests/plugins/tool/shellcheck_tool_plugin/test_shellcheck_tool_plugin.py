"""Unit tests for the Shellcheck tool plugin."""
import argparse
import os
import subprocess
import sys

import mock
import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.shellcheck_tool_plugin import ShellcheckToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_shellcheck_tool_plugin(binary=None):
    """Construct and return an instance of the Shellcheck plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--shellcheck-bin", dest="shellcheck_bin")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    sctp = ShellcheckToolPlugin()
    if binary:
        plugin_context.args.shellcheck_bin = binary
    sctp.set_plugin_context(plugin_context)
    return sctp


def test_shellcheck_tool_plugin_found():
    """Test that the plugin manager finds the Shellcheck plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {
            "Tool": ToolPlugin,
        }
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "shellcheck"
    assert any(
        plugin_info.plugin_object.get_name() == "shellcheck"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Shellcheck Tool Plugin
    assert any(
        plugin_info.name == "Shellcheck Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_shellcheck_tool_plugin_scan_valid():
    """Integration test: Make sure the shellcheck output hasn't changed."""
    sctp = setup_shellcheck_tool_plugin()
    # Sanity check - make sure shellcheck exists
    if not sctp.command_exists("shellcheck"):
        pytest.skip("Couldn't find 'shellcheck' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run shellcheck on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["shell_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "basic.sh")
    ]
    issues = sctp.scan(package, "level")
    assert len(issues) == 2


def test_shellcheck_tool_plugin_no_sources():
    """Make sure no issues are found if no sources are provided.

    Expected result: issues is empty
    """
    sctp = setup_shellcheck_tool_plugin()
    # Sanity check - make sure shellcheck exists
    if not sctp.command_exists("shellcheck"):
        pytest.skip("Couldn't find 'shellcheck' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run shellcheck on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["shell_src"] = []
    issues = sctp.scan(package, "level")
    assert not issues


def test_spellcheck_tool_plugin_scan_wrong_binary():
    """
    Test what happens when the specified tool binary does not exist.

    Expected result: issues is None
    """
    sctp = setup_shellcheck_tool_plugin("wrong_binary")
    # Sanity check - make sure shellcheck exists
    if not sctp.command_exists("shellcheck"):
        pytest.skip("Couldn't find 'shellcheck' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run shellcheck on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["shell_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "basic.sh")
    ]
    issues = sctp.scan(package, "level")
    assert issues is None


def test_shellcheck_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of shellcheck."""
    sctp = setup_shellcheck_tool_plugin()
    output = [
        {
            "file": "/home/user/basic.sh",
            "line": 3,
            "endLine": 3,
            "column": 1,
            "endColumn": 12,
            "level": "warning",
            "code": 2164,
            "message": "Use 'cd ... || exit' or 'cd ... || return' in case cd fails.",
            "fix": {
                "replacements": [
                    {
                        "line": 3,
                        "endLine": 3,
                        "precedence": 5,
                        "insertionPoint": "beforeStart",
                        "column": 12,
                        "replacement": " || exit",
                        "endColumn": 12,
                    }
                ]
            },
        }
    ]
    issues = sctp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/basic.sh"
    assert issues[0].line_number == "3"
    assert issues[0].tool == "shellcheck"
    assert issues[0].issue_type == "SC2164"
    assert issues[0].severity == "3"
    assert (
        issues[0].message
        == "Use 'cd ... || exit' or 'cd ... || return' in case cd fails."
    )

    output = [
        {
            "file": "/home/user/basic.bash",
            "line": 4,
            "endLine": 4,
            "column": 3,
            "endColumn": 44,
            "level": "info",
            "code": 1091,
            "message": "Not following: ./devel/setup.bash was not specified as input (see shellcheck -x).",
            "fix": None,
        }
    ]
    issues = sctp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/basic.bash"
    assert issues[0].line_number == "4"
    assert issues[0].tool == "shellcheck"
    assert issues[0].issue_type == "SC1091"
    assert issues[0].severity == "1"
    assert (
        issues[0].message
        == "Not following: ./devel/setup.bash was not specified as input (see shellcheck -x)."
    )

    output = [
        {
            "file": "/home/user/basic.bash",
            "line": 9,
            "endLine": 9,
            "column": 3,
            "endColumn": 44,
            "level": "style",
            "code": 1091,
            "message": "Not following: ./devel/setup.bash was not specified as input (see shellcheck -x).",
            "fix": None,
        }
    ]
    issues = sctp.parse_output(output)
    assert issues[0].severity == "1"

    output = [
        {
            "file": "/home/user/basic.bash",
            "line": 9,
            "endLine": 9,
            "column": 3,
            "endColumn": 44,
            "level": "error",
            "code": 1091,
            "message": "Not following: ./devel/setup.bash was not specified as input (see shellcheck -x).",
            "fix": None,
        }
    ]
    issues = sctp.parse_output(output)
    assert issues[0].severity == "5"

    output = [
        {
            "file": "/home/user/basic.bash",
            "line": 9,
            "endLine": 9,
            "column": 3,
            "endColumn": 44,
            "level": "unsupported level",
            "code": 1091,
            "message": "Not following: ./devel/setup.bash was not specified as input (see shellcheck -x).",
            "fix": None,
        }
    ]
    issues = sctp.parse_output(output)
    assert issues[0].severity == "3"

    output = [{"field": "not a real field",}]
    issues = sctp.parse_output(output)
    assert not issues


def test_shellcheck_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of shellcheck."""
    sctp = setup_shellcheck_tool_plugin()
    output = "invalid text"
    issues = sctp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.shellcheck_tool_plugin.subprocess.check_output")
def test_shellcheck_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means shellcheck hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    sctp = setup_shellcheck_tool_plugin()
    # Sanity check - make sure shellcheck exists
    if not sctp.command_exists("shellcheck"):
        pytest.skip("Couldn't find 'shellcheck' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run shellcheck on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["shell_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "shellcheck_test.sh")
    ]
    issues = sctp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = sctp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.shellcheck_tool_plugin.subprocess.check_output")
def test_shellcheck_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means shellcheck doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    sctp = setup_shellcheck_tool_plugin()
    # Sanity check - make sure shellcheck exists
    if not sctp.command_exists("shellcheck"):
        pytest.skip("Couldn't find 'shellcheck' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run shellcheck on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["shell_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "shellcheck_test.sh")
    ]
    issues = sctp.scan(package, "level")
    assert issues is None
