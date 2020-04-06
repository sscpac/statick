"""Unit tests for the cpplint plugin."""
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
from statick_tool.plugins.tool.cpplint_tool_plugin import CpplintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin

try:
    from tempfile import TemporaryDirectory
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from backports.tempfile import (
        TemporaryDirectory,
    )  # pylint: disable=wrong-import-order


def setup_cpplint_tool_plugin():
    """Initialize and return an instance of the cpplint plugin."""
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
    ctp = CpplintToolPlugin()
    ctp.set_plugin_context(plugin_context)
    return ctp


def test_cpplint_tool_plugin_found():
    """Test that the plugin manager can find the cpplint plugin."""
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
    # Verify that a plugin's get_name() function returns "cpplint"
    assert any(
        plugin_info.plugin_object.get_name() == "cpplint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Cpplint Tool Plugin
    assert any(
        plugin_info.name == "Cpplint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_cpplint_tool_plugin_scan_valid():
    """Integration test: Make sure the cpplint output hasn't changed."""
    ctp = setup_cpplint_tool_plugin()
    if not ctp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test cpplint plugin")
    elif not ctp.command_exists("cpplint"):
        pytest.skip("Can't find cpplint, unable to test cpplint plugin")
    elif sys.platform == "win32":
        pytest.skip("Don't know how to run cpplint on Windows.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    # Need to actually run CMake to generate compile_commands.json
    with TemporaryDirectory() as bin_dir:
        try:
            subprocess.check_output(
                [
                    "cmake",
                    os.path.join(os.path.dirname(__file__), "valid_package"),
                    "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                    "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                    "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=" + bin_dir,
                ],
                universal_newlines=True,
                cwd=bin_dir,
            )
        except subprocess.CalledProcessError as ex:
            print("Problem running CMake! Returncode = {}".format(str(ex.returncode)))
            print("{}".format(ex.output))
            pytest.fail("Failed running CMake")

        package["make_targets"] = []
        package["make_targets"].append({})
        package["make_targets"][0]["src"] = [
            os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
        ]
        package["headers"] = []
        package["cpplint"] = "cpplint"
        issues = ctp.scan(package, "level")
    print("Line: {}".format(issues[2].message))
    assert len(issues) == 4
    assert issues[2].filename == os.path.join(
        os.path.dirname(__file__), "valid_package", "test.c"
    )
    assert issues[2].line_number == "6"
    assert issues[2].tool == "cpplint"
    assert issues[2].issue_type == "whitespace/line_length"
    assert issues[2].severity == "2"
    assert issues[2].message == " Lines should be <= 80 characters long "


def test_tool_dependencies():
    """Verify that tool dependencies are reported correctly."""
    ctp = setup_cpplint_tool_plugin()
    assert ctp.get_tool_dependencies() == ["make"]


def test_cpplint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of cpplint."""
    ctp = setup_cpplint_tool_plugin()
    output = (
        "{}:14: Redundant blank line at the end of a code block should be deleted. "
        "[whitespace/blank_line] [3]".format(os.path.join("valid_package", "test.c"))
    )
    issues = ctp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == os.path.join("valid_package", "test.c")
    assert issues[0].line_number == "14"
    assert issues[0].tool == "cpplint"
    assert issues[0].issue_type == "whitespace/blank_line"
    assert issues[0].severity == "3"
    assert (
        issues[0].message
        == "Redundant blank line at the end of a code block should be deleted."
    )


def test_cpplint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of cpplint."""
    ctp = setup_cpplint_tool_plugin()
    output = "invalid text"
    issues = ctp.parse_output(output)
    assert not issues


def test_cpplint_tool_plugin_scan_missing_fields():
    """
    Test what happens when key fields are missing from the Package argument.

    Expected result: issues is None then empty
    """
    ctp = setup_cpplint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Missing tool name in package.
    issues = ctp.scan(package, "level")
    assert issues is None

    # Missing make_targets and headers in package
    package["cpplint"] = "cpplint"
    issues = ctp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.cpplint_tool_plugin.subprocess.check_output")
def test_cpplint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means cpplint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    ctp = setup_cpplint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    package["cpplint"] = "cpplint"
    issues = ctp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.cpplint_tool_plugin.subprocess.check_output")
def test_cpplint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means cpplint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    ctp = setup_cpplint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    package["cpplint"] = "cpplint"
    issues = ctp.scan(package, "level")
    assert issues is None


def test_checkforexceptions_true():
    """Test check_for_exceptions behavior where it should return True."""
    mm = mock.MagicMock()
    mm.group.side_effect = (
        lambda i: "test.cpp" if i == 1 else "build/namespaces" if i == 4 else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = (
        lambda i: "test.cc" if i == 1 else "build/namespaces" if i == 4 else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = (
        lambda i: "not-a-file"
        if i == 1
        else "unnamed"
        if i == 3
        else "build/namespaces"
        if i == 4
        else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = (
        lambda i: "cfg/cpp/Config.h"
        if i == 1
        else "build/storage_class"
        if i == 4
        else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)


def test_checkforexceptions_false():
    """Test check_for_exceptions behavior where it should return False."""
    mm = mock.MagicMock()
    mm.group.side_effect = (
        lambda i: "test.h"
        if i == 1
        else "google-build-using-namespace"
        if i == 6
        else False
    )
    assert not CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = (
        lambda i: "test.cpp" if i == 1 else "some-other-error" if i == 6 else False
    )
    assert not CpplintToolPlugin.check_for_exceptions(mm)
