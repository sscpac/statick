"""Unit tests for the cpplint plugin."""

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
from statick_tool.plugins.tool.cpplint import CpplintToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from tempfile import TemporaryDirectory


def setup_cpplint_tool_plugin():
    """Initialize and return an instance of the cpplint plugin."""
    arg_parser = argparse.ArgumentParser()

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
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "cpplint" for _, plugin in list(plugins.items())
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
            print(f"Problem running CMake! Returncode = {str(ex.returncode)}")
            print(f"{ex.output}")
            pytest.fail("Failed running CMake")

        package["make_targets"] = []
        package["make_targets"].append({})
        package["make_targets"][0]["src"] = [
            os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
        ]
        package["headers"] = []
        package["cpplint"] = "cpplint"
        issues = ctp.scan(package, "level")
    print(f"Line: {issues[2].message}")
    assert len(issues) == 5
    assert issues[2].filename == os.path.join(
        os.path.dirname(__file__), "valid_package", "test.c"
    )
    assert issues[2].line_number == "6"
    assert issues[2].tool == "cpplint"
    assert issues[2].issue_type == "whitespace/line_length"
    assert issues[2].severity == "2"
    assert issues[2].message == " Lines should be <= 80 characters long "


def test_cpplint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of cpplint."""
    ctp = setup_cpplint_tool_plugin()
    output = (
        "{}:14: Redundant blank line at the end of a code block should be deleted. "
        "[whitespace/blank_line] [3]".format(os.path.join("valid_package", "test.c"))
    )
    issues = ctp.parse_tool_output(output)
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
    issues = ctp.parse_tool_output(output)
    assert not issues


def test_cpplint_tool_plugin_scan_missing_fields():
    """Test what happens when key fields are missing from the Package argument.

    Expected result: issues is None then empty
    """
    ctp = setup_cpplint_tool_plugin()

    # Missing tool name in package.
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    issues = ctp.scan(package, "level")
    assert issues is None

    # Empty make_targets and headers in package.
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["headers"] = []
    issues = ctp.scan(package, "level")
    assert not issues

    # Missing make_targets and headers in package.
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = ctp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.cpplint.subprocess.check_output")
def test_cpplint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means cpplint doesn't
    exist).

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


@mock.patch("statick_tool.plugins.tool.cpplint.subprocess.check_output")
def test_cpplint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means cpplint hit
    an error).

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
    mm.group.side_effect = lambda i: (
        "test.cpp" if i == 1 else "build/namespaces" if i == 4 else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = lambda i: (
        "test.cc" if i == 1 else "build/namespaces" if i == 4 else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = lambda i: (
        "not-a-file"
        if i == 1
        else "unnamed" if i == 3 else "build/namespaces" if i == 4 else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = lambda i: (
        "cfg/cpp/Config.h" if i == 1 else "build/storage_class" if i == 4 else False
    )
    assert CpplintToolPlugin.check_for_exceptions(mm)


def test_checkforexceptions_false():
    """Test check_for_exceptions behavior where it should return False."""
    mm = mock.MagicMock()
    mm.group.side_effect = lambda i: (
        "test.h" if i == 1 else "google-build-using-namespace" if i == 6 else False
    )
    assert not CpplintToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = lambda i: (
        "test.cpp" if i == 1 else "some-other-error" if i == 6 else False
    )
    assert not CpplintToolPlugin.check_for_exceptions(mm)
