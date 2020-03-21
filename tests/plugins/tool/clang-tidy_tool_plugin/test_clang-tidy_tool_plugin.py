"""Unit tests for the clang-tidy plugin."""
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
from statick_tool.plugins.tool.clang_tidy_tool_plugin import ClangTidyToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin

try:
    from tempfile import TemporaryDirectory
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from backports.tempfile import (
        TemporaryDirectory,
    )  # pylint: disable=wrong-import-order


def setup_clang_tidy_tool_plugin(use_plugin_context=True):
    """Initialize and return an instance of the clang-tidy plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--clang-tidy-bin", dest="clang_tidy_bin")
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    cttp = ClangTidyToolPlugin()
    if use_plugin_context:
        cttp.set_plugin_context(plugin_context)
    return cttp


def test_clang_tidy_tool_plugin_found():
    """Test that the plugin manager can find the clang-tidy plugin."""
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
    # Verify that a plugin's get_name() function returns "clang_tidy"
    assert any(
        plugin_info.plugin_object.get_name() == "clang-tidy"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named ClangTidy Tool Plugin
    assert any(
        plugin_info.name == "clang-tidy Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_clang_tidy_tool_plugin_scan_valid():
    """Integration test: Make sure the clang_tidy output hasn't changed."""
    cttp = setup_clang_tidy_tool_plugin()
    if not cttp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test clang_tidy plugin")
    elif not cttp.command_exists("clang-tidy"):
        pytest.skip("Can't find clang-tidy, unable to test clang_tidy plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    # Need to run CMake
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
        package["bin_dir"] = bin_dir
        package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
        issues = cttp.scan(package, "level")
    assert len(issues) == 1
    assert issues[0].filename == os.path.join(
        os.path.dirname(__file__), "valid_package", "test.c"
    )
    assert issues[0].line_number == "6"
    assert issues[0].tool == "clang-tidy"
    assert issues[0].issue_type == "warning/clang-analyzer-deadcode.DeadStores"
    assert issues[0].severity == "3"
    assert issues[0].message == "Value stored to 'si' is never read"


def test_clang_tidy_tool_plugin_scan_no_plugin_context():
    """Test that issues are None when no plugin context is provided."""
    cttp = setup_clang_tidy_tool_plugin(False)
    if not cttp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test clang_tidy plugin")
    elif not cttp.command_exists("clang-tidy"):
        pytest.skip("Can't find clang-tidy, unable to test clang_tidy plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    with TemporaryDirectory() as bin_dir:
        package["bin_dir"] = bin_dir
    package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
    issues = cttp.scan(package, "level")
    assert not issues


def test_clang_tidy_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of clang_tidy."""
    cttp = setup_clang_tidy_tool_plugin()
    output = "{}:6:5: warning: Value stored to 'si' is never read [clang-analyzer-deadcode.DeadStores]".format(
        os.path.join("valid_package", "test.c")
    )
    issues = cttp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == os.path.join("valid_package", "test.c")
    assert issues[0].line_number == "6"
    assert issues[0].tool == "clang-tidy"
    assert issues[0].issue_type == "warning/clang-analyzer-deadcode.DeadStores"
    assert issues[0].severity == "3"
    assert issues[0].message == "Value stored to 'si' is never read"


def test_clang_tidy_tool_plugin_parse_note():
    """
    Verify that we ignore 'note' lines of clang-tidy.

    Expected output: Empty list
    """
    cttp = setup_clang_tidy_tool_plugin()
    output = "{}:6:5: note: Value stored to 'si' is never read".format(
        os.path.join("valid_package", "test.c")
    )
    issues = cttp.parse_output(output)
    assert not issues


def test_clang_tidy_tool_plugin_parse_star():
    """
    Verify that we ignore *-prefixed lines of clang-tidy.

    Expected output: Empty list
    """
    cttp = setup_clang_tidy_tool_plugin()
    output = " * {}:6:5: warning: Value stored to 'si' is never read [clang-analyzer-deadcode.DeadStores]".format(
        os.path.join("valid_package", "test.c")
    )
    issues = cttp.parse_output(output)
    assert not issues


def test_clang_tidy_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of clang_tidy."""
    cttp = setup_clang_tidy_tool_plugin()
    output = "invalid text"
    issues = cttp.parse_output(output)
    assert not issues


def test_clang_tidy_tool_plugin_scan_missing_fields():
    """
    Test what happens when key fields are missing from the Package argument.

    Expected result: issues is empty
    """
    cttp = setup_clang_tidy_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Missing bin_dir
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
    issues = cttp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.clang_tidy_tool_plugin.subprocess.check_output")
def test_clang_tidy_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means clang-tidy doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cttp = setup_clang_tidy_tool_plugin()
    with TemporaryDirectory() as bin_dir:
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        package["make_targets"] = []
        package["make_targets"].append({})
        package["make_targets"][0]["src"] = [
            os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
        ]
        package["bin_dir"] = bin_dir
        package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
        issues = cttp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.clang_tidy_tool_plugin.subprocess.check_output")
def test_clang_tidy_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means clang-tidy hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    cttp = setup_clang_tidy_tool_plugin()
    with TemporaryDirectory() as bin_dir:
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        package["make_targets"] = []
        package["make_targets"].append({})
        package["make_targets"][0]["src"] = [
            os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
        ]
        package["bin_dir"] = bin_dir
        package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
        issues = cttp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.clang_tidy_tool_plugin.subprocess.check_output")
def test_clang_tidy_tool_plugin_scan_diagnosticerror(mock_subprocess_check_output):
    """
    Test that a CalledProcessError is raised when subprocess's output contains 'clang-diagnostic-error'.

    Expected result: issues is None
    """
    mock_subprocess_check_output.return_value = "clang-diagnostic-error"
    cttp = setup_clang_tidy_tool_plugin()
    with TemporaryDirectory() as bin_dir:
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        package["make_targets"] = []
        package["make_targets"].append({})
        package["make_targets"][0]["src"] = [
            os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
        ]
        package["bin_dir"] = bin_dir
        package["src_dir"] = os.path.join(os.path.dirname(__file__), "valid_package")
        issues = cttp.scan(package, "level")
    assert issues is None


def test_checkforexceptions_true():
    """Test check_for_exceptions behavior where it should return True."""
    mm = mock.MagicMock()
    mm.group.side_effect = (
        lambda i: "test.cpp"
        if i == 1
        else "google-build-using-namespace"
        if i == 6
        else False
    )
    assert ClangTidyToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = (
        lambda i: "test.cc"
        if i == 1
        else "google-build-using-namespace"
        if i == 6
        else False
    )
    assert ClangTidyToolPlugin.check_for_exceptions(mm)


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
    assert not ClangTidyToolPlugin.check_for_exceptions(mm)
    mm.group.side_effect = (
        lambda i: "test.cpp" if i == 1 else "some-other-error" if i == 6 else False
    )
    assert not ClangTidyToolPlugin.check_for_exceptions(mm)
