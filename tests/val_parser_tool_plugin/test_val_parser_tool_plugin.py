"""Unit tests for the Parser tool plugin."""
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
from statick_tool.plugins.tool.val_parser_tool_plugin import ValParserToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_val_parser_tool_plugin(binary=None):
    """Construct and return an instance of the Parser plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--val-parser-bin", dest="val_parser_bin")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    vtp = ValParserToolPlugin()
    if binary:
        plugin_context.args.val_parser_bin = binary
    vtp.set_plugin_context(plugin_context)
    return vtp


def test_val_parser_tool_plugin_found():
    """Test that the plugin manager finds the Parser plugin."""
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
    # Verify that a plugin's get_name() function returns "val_parser"
    assert any(
        plugin_info.plugin_object.get_name() == "val_parser"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Parser Tool Plugin
    assert any(
        plugin_info.name == "VAL Parser Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_val_parser_tool_plugin_gather_args():
    """Test that the Parser tool plugin arguments are collected."""
    arg_parser = argparse.ArgumentParser()
    vtp = setup_val_parser_tool_plugin()
    vtp.gather_args(arg_parser)


def test_val_parser_tool_plugin_scan_valid():
    """Integration test: Make sure the Parser output hasn't changed."""
    vtp = setup_val_parser_tool_plugin("/opt/val/bin/Parser")
    # Sanity check - make sure Parser exists
    if not vtp.command_exists("/opt/val/bin/Parser"):
        pytest.skip("Couldn't find 'Parser' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run Parser on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["pddl_domain_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "domain.pddl"),
    ]
    package["pddl_problem_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "problem.pddl"),
    ]
    issues = vtp.scan(package, "level")
    assert not issues


def test_val_parser_tool_plugin_scan_find_errors():
    """Make sure the Parser tool correctly finds errors."""
    vtp = setup_val_parser_tool_plugin("/opt/val/bin/Parser")
    # Sanity check - make sure Parser exists
    if not vtp.command_exists("/opt/val/bin/Parser"):
        pytest.skip("Couldn't find 'Parser' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run Parser on Windows.")
    package = Package(
        "error_package", os.path.join(os.path.dirname(__file__), "error_package")
    )
    package["pddl_domain_src"] = [
        os.path.join(os.path.dirname(__file__), "error_package", "domain.pddl"),
    ]
    package["pddl_problem_src"] = [
        os.path.join(os.path.dirname(__file__), "error_package", "problem.pddl"),
    ]
    issues = vtp.scan(package, "level")
    assert len(issues) == 7

    assert issues[0].filename == os.path.join(
        os.path.dirname(__file__), "error_package", "domain.pddl"
    )
    assert issues[0].line_number == "7"
    assert issues[0].tool == "val_parser"
    assert issues[0].issue_type == "PDDL"
    assert issues[0].severity == "5"
    assert issues[0].message == "Syntax error in domain"

    assert issues[1].filename == os.path.join(
        os.path.dirname(__file__), "error_package", "problem.pddl"
    )
    assert issues[1].line_number == "22"
    assert issues[1].tool == "val_parser"
    assert issues[1].issue_type == "PDDL"
    assert issues[1].severity == "3"
    assert issues[1].message == "Undeclared symbol: room"

    assert issues[2].filename == os.path.join(
        os.path.dirname(__file__), "error_package", "problem.pddl"
    )
    assert issues[2].line_number == "24"
    assert issues[2].tool == "val_parser"
    assert issues[2].issue_type == "PDDL"
    assert issues[2].severity == "3"
    assert issues[2].message == "Undeclared symbol: ball"


def test_val_parser_tool_plugin_no_sources():
    """Make sure no issues are found if no sources are provided.

    Expected result: issues is empty
    """
    vtp = setup_val_parser_tool_plugin("/opt/val/bin/Parser")
    # Sanity check - make sure Parser exists
    if not vtp.command_exists("/opt/val/bin/Parser"):
        pytest.skip("Couldn't find 'Parser' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run Parser on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["pddl_domain_src"] = []
    issues = vtp.scan(package, "level")
    assert not issues


def test_val_parser_tool_plugin_scan_wrong_binary():
    """
    Test what happens when the specified tool binary does not exist.

    Expected result: issues is None
    """
    vtp = setup_val_parser_tool_plugin("wrong_binary")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["pddl_domain_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "domain.pddl"),
    ]
    package["pddl_problem_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "problem.pddl"),
    ]
    issues = vtp.scan(package, "level")
    assert issues is None


def test_val_parser_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of Parser."""
    vtp = setup_val_parser_tool_plugin()
    output = ""
    issues = vtp.parse_output(output)
    assert not issues

    output = "Errors: 0, warnings: 0"
    issues = vtp.parse_output(output)
    assert not issues

    output = ""
    line = "Errors: 1, warnings: 1\n"
    output += line
    line = "/tmp/dummy_package/domain.pddl: line: 83: Error: Syntax error in domain\n"
    output += line
    line = "/tmp/dummy_package/problem.pddl: line: 42: Warning: Undeclared symbol: x"
    output += line
    issues = vtp.parse_output(output)
    assert len(issues) == 2
    assert issues[0].filename == "/tmp/dummy_package/domain.pddl"
    assert issues[0].line_number == "83"
    assert issues[0].tool == "val_parser"
    assert issues[0].issue_type == "PDDL"
    assert issues[0].severity == "5"
    assert issues[0].message == "Syntax error in domain"
    assert issues[1].filename == "/tmp/dummy_package/problem.pddl"
    assert issues[1].line_number == "42"
    assert issues[1].tool == "val_parser"
    assert issues[1].issue_type == "PDDL"
    assert issues[1].severity == "3"
    assert issues[1].message == "Undeclared symbol: x"


def test_val_parser_tool_plugin_parse_invalid():
    """Verify that we can parse the invalid output of Parser."""
    vtp = setup_val_parser_tool_plugin()
    output = "invalid text"
    issues = vtp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.val_parser_tool_plugin.subprocess.check_output")
def test_val_parser_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means Parser hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    vtp = setup_val_parser_tool_plugin()
    # Sanity check - make sure Parser exists
    if not vtp.command_exists("/opt/val/bin/Parser"):
        pytest.skip("Couldn't find 'Parser' command, can't run tests")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["pddl_domain_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "domain.pddl"),
    ]
    package["pddl_problem_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "problem.pddl"),
    ]
    issues = vtp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = vtp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.val_parser_tool_plugin.subprocess.check_output")
def test_val_parser_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means Parser doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    vtp = setup_val_parser_tool_plugin()
    # Sanity check - make sure Parser exists
    if not vtp.command_exists("/opt/val/bin/Parser"):
        pytest.skip("Couldn't find 'Parser' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run Parser on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["pddl_domain_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "domain.pddl"),
    ]
    package["pddl_problem_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "problem.pddl"),
    ]
    issues = vtp.scan(package, "level")
    assert issues is None
