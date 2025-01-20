"""Unit tests for the Validate tool plugin."""
import argparse
import os
import subprocess
import sys

import mock
import pytest
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources

import statick_tool
from statick_tool.plugins.tool.val_validate import ValValidateToolPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_val_validate_tool_plugin(binary=None):
    """Construct and return an instance of the Validate plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--val-validate-bin", dest="val_validate_bin")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    vtp = ValValidateToolPlugin()
    print(f"binary: {binary}")
    if binary:
        plugin_context.args.val_validate_bin = binary
    vtp.set_plugin_context(plugin_context)
    return vtp


def test_val_validate_tool_plugin_found():
    """Test that the plugin manager finds the Validate plugin."""
    tool_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        tool_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "val_validate" for _, plugin in list(tool_plugins.items())
    )


def test_val_validate_tool_plugin_gather_args():
    """Test that the Validate tool plugin arguments are collected."""
    arg_parser = argparse.ArgumentParser()
    vtp = setup_val_validate_tool_plugin()
    vtp.gather_args(arg_parser)


def test_val_validate_tool_plugin_scan_valid():
    """Integration test: Make sure the Validate output hasn't changed."""
    vtp = setup_val_validate_tool_plugin("/opt/val/bin/Validate")
    # Sanity check - make sure Validate exists
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
    assert not issues

    try:
        os.remove(os.path.join(os.getcwd(), "val_validate.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


def test_val_validate_tool_plugin_no_sources():
    """Make sure no issues are found if no sources are provided.

    Expected result: issues is empty
    """
    vtp = setup_val_validate_tool_plugin("/opt/val/bin/Validate")
    # Sanity check - make sure Validate exists
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

    try:
        os.remove(os.path.join(os.getcwd(), "val_validate.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


def test_val_validate_tool_plugin_scan_wrong_binary():
    """
    Test what happens when the specified tool binary does not exist.

    Expected result: issues is None
    """
    vtp = setup_val_validate_tool_plugin("wrong_binary")
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

    try:
        os.remove(os.path.join(os.getcwd(), "val_validate.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


def test_val_validate_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of Validate."""
    vtp = setup_val_validate_tool_plugin()
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
    issues = vtp.parse_tool_output(output, "test.pddl")
    assert not issues

    output = "Errors: 0, warnings: 0"
    issues = vtp.parse_tool_output(output, "test.pddl")
    assert not issues

    output = "Error: Parser failed to read file!"
    issues = vtp.parse_tool_output(output, "/home/user/test.pddl")
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/test.pddl"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "val_validate"
    assert issues[0].issue_type == "0"
    assert issues[0].severity == "3"
    assert (
        issues[0].message
        == "Exact file and line number unknown. Parser failed to read file!"
    )

    output = "Problem in domain definition!"
    issues = vtp.parse_tool_output(output, "/home/user/test.pddl")
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/test.pddl"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "val_validate"
    assert issues[0].issue_type == "1"
    assert issues[0].severity == "3"
    assert (
        issues[0].message
        == "Exact file and line number unknown. Problem in domain definition!"
    )


def test_val_validate_tool_plugin_parse_invalid():
    """Verify that we can parse the invalid output of Validate."""
    vtp = setup_val_validate_tool_plugin()
    output = "invalid text"
    issues = vtp.parse_tool_output(output, "test.pddl")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.val_validate.subprocess.check_output"
)
def test_val_validate_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means Validate hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    vtp = setup_val_validate_tool_plugin()
    # Sanity check - make sure Validate exists
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

    try:
        os.remove(os.path.join(os.getcwd(), "val_validate.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")


@mock.patch(
    "statick_tool.plugins.tool.val_validate.subprocess.check_output"
)
def test_val_validate_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means Validate doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    vtp = setup_val_validate_tool_plugin()
    # Sanity check - make sure Validate exists
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

    try:
        os.remove(os.path.join(os.getcwd(), "val_validate.log"))
    except FileNotFoundError as ex:
        print(f"Error: {ex}")
    except OSError as ex:
        print(f"Error: {ex}")
