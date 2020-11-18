"""Unit tests for the VAL tool plugin."""
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
from statick_tool.plugins.tool.val_tool_plugin import ValToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_val_tool_plugin(binary=None):
    """Construct and return an instance of the VAL plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--val-bin", dest="val_bin")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    vtp = ValToolPlugin()
    if binary:
        plugin_context.args.val_bin = binary
    vtp.set_plugin_context(plugin_context)
    return vtp


def test_val_tool_plugin_found():
    """Test that the plugin manager finds the VAL plugin."""
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
    # Verify that a plugin's get_name() function returns "val"
    assert any(
        plugin_info.plugin_object.get_name() == "val"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named VAL Tool Plugin
    assert any(
        plugin_info.name == "VAL Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_val_tool_plugin_gather_args():
    """Test that the VAL tool plugin arguments are collected."""
    arg_parser = argparse.ArgumentParser()
    vtp = setup_val_tool_plugin()
    vtp.gather_args(arg_parser)


def test_val_tool_plugin_scan_valid():
    """Integration test: Make sure the val output hasn't changed."""
    vtp = setup_val_tool_plugin("/opt/val/bin/Validate")
    # Sanity check - make sure val exists
    if not vtp.command_exists("/opt/val/bin/Validate"):
        pytest.skip("Couldn't find 'Validate' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run val on Windows.")
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


def test_val_tool_plugin_no_sources():
    """Make sure no issues are found if no sources are provided.

    Expected result: issues is empty
    """
    vtp = setup_val_tool_plugin("/opt/val/bin/Validate")
    # Sanity check - make sure val exists
    if not vtp.command_exists("/opt/val/bin/Validate"):
        pytest.skip("Couldn't find 'Validate' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run Validate on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["pddl_domain_src"] = []
    issues = vtp.scan(package, "level")
    assert not issues


def test_spellcheck_tool_plugin_scan_wrong_binary():
    """
    Test what happens when the specified tool binary does not exist.

    Expected result: issues is None
    """
    vtp = setup_val_tool_plugin("wrong_binary")
    # Sanity check - make sure val exists
    if not vtp.command_exists("/opt/val/bin/Validate"):
        pytest.skip("Couldn't find 'Validate' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run Validate on Windows.")
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


def test_val_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of val."""
    vtp = setup_val_tool_plugin()
    output = ""
    line = "Type-checking move-up"
    output += line
    line = "...action passes type checking."
    output += line
    line = "Type-checking move-down"
    output += line
    line = "...action passes type checking."
    output += line
    line = "Type-checking board"
    output += line
    line = "...action passes type checking."
    output += line
    line = "Type-checking leave"
    output += line
    line = "...action passes type checking."
    output += line
    issues = vtp.parse_output(output, "test.pddl")
    assert not issues

    output = "Errors: 0, warnings: 0"
    issues = vtp.parse_output(output, "test.pddl")
    assert not issues

    output = "Error: Parser failed to read file!"
    issues = vtp.parse_output(output, "/home/user/test.pddl")
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/test.pddl"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "val"
    assert issues[0].issue_type == "0"
    assert issues[0].severity == "3"
    assert (
        issues[0].message
        == "Exact file and line number unknown. Parser failed to read file!"
    )

    output = "Problem in domain definition!"
    issues = vtp.parse_output(output, "/home/user/test.pddl")
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/test.pddl"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "val"
    assert issues[0].issue_type == "1"
    assert issues[0].severity == "3"
    assert (
        issues[0].message
        == "Exact file and line number unknown. Problem in domain definition!"
    )


def test_val_tool_plugin_parse_invalid():
    """Verify that we can parse the invalid output of val."""
    vtp = setup_val_tool_plugin()
    output = "invalid text"
    issues = vtp.parse_output(output, "test.pddl")
    assert not issues


@mock.patch("statick_tool.plugins.tool.val_tool_plugin.subprocess.check_output")
def test_val_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means val hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    vtp = setup_val_tool_plugin()
    # Sanity check - make sure val exists
    if not vtp.command_exists("/opt/val/bin/Validate"):
        pytest.skip("Couldn't find 'Validate' command, can't run tests")
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


@mock.patch("statick_tool.plugins.tool.val_tool_plugin.subprocess.check_output")
def test_val_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means val doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    vtp = setup_val_tool_plugin()
    # Sanity check - make sure val exists
    if not vtp.command_exists("/opt/val/bin/Validate"):
        pytest.skip("Couldn't find 'Validate' command, can't run tests")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run val on Windows.")
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
