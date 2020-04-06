"""Unit tests for the catkin_lint tool plugin."""
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
from statick_tool.plugins.tool.catkin_lint_tool_plugin import CatkinLintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_catkin_lint_tool_plugin():
    """Construct and return an instance of the CatkinLint plugin."""
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
    cltp = CatkinLintToolPlugin()
    cltp.set_plugin_context(plugin_context)
    return cltp


def test_catkin_lint_tool_plugin_found():
    """Test that the plugin manager finds the CatkinLint plugin."""
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
    # Verify that a plugin's get_name() function returns "catkin_lint"
    assert any(
        plugin_info.plugin_object.get_name() == "catkin_lint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Yamllint Tool Plugin
    assert any(
        plugin_info.name == "Catkin Lint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_catkin_lint_tool_plugin_scan_valid():
    """Integration test: Make sure the catkin_lint output hasn't changed."""
    cltp = setup_catkin_lint_tool_plugin()
    if not cltp.command_exists("catkin_lint"):
        pytest.skip("Missing catkin_lint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.scan(package, "level")
    assert len(issues) == 1


def test_catkin_lint_tool_plugin_scan_missing_name():
    """
    Test with missing tool name.

    Expected result: issues is empty
    """
    cltp = setup_catkin_lint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = cltp.scan(package, "level")
    assert not issues


def test_catkin_lint_tool_plugin_scan_c0x():
    """Scan a package that sets compiler flags for c++0x"""
    cltp = setup_catkin_lint_tool_plugin()
    if not cltp.command_exists("catkin_lint"):
        pytest.skip("Missing catkin_lint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "c0x_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.scan(package, "level")
    assert len(issues) == 1


def test_catkin_lint_tool_plugin_scan_c11():
    """Scan a package that sets compiler flags for c++11"""
    cltp = setup_catkin_lint_tool_plugin()
    if not cltp.command_exists("catkin_lint"):
        pytest.skip("Missing catkin_lint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "c11_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.scan(package, "level")
    assert len(issues) == 1


def test_catkin_lint_tool_plugin_scan_gnu99():
    """Scan a package that sets compiler flags for gnu99"""
    cltp = setup_catkin_lint_tool_plugin()
    if not cltp.command_exists("catkin_lint"):
        pytest.skip("Missing catkin_lint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "gnu99_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.scan(package, "level")
    assert len(issues) == 1


def test_catkin_lint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of catkin_lint."""
    cltp = setup_catkin_lint_tool_plugin()
    output = "custom_pkg: notice: use ${PROJECT_NAME} instead of 'custom_pkg'"
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.parse_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == os.path.join(package.path, "package.xml")
    assert issues[0].line_number == "1"
    assert issues[0].tool == "catkin_lint"
    assert issues[0].issue_type == "notice"
    assert issues[0].severity == "1"
    assert (
        issues[0].message == "use ${PROJECT_NAME} instead of 'custom_pkg' "
        "(I can't really tell if this applies for "
        "package.xml or CMakeLists.txt. Make sure to "
        "check both for this issue)"
    )

    output = "custom_pkg: warning: target 'custom_target' is not installed"
    issues = cltp.parse_output(package, output)
    assert issues[0].severity == "3"

    output = "custom_pkg: error: missing build_depend on 'catkin'"
    issues = cltp.parse_output(package, output)
    assert issues[0].severity == "5"

    output = "custom_pkg: notice: missing build_depend on 'rostest'"
    issues = cltp.parse_output(package, output)
    assert (
        issues[0].message == "missing test_depend on 'rostest' "
        "(I can't really tell if this applies for "
        "package.xml or CMakeLists.txt. Make sure to "
        "check both for this issue)"
    )

    output = "custom_pkg: notice: unconfigured build_depend on"
    issues = cltp.parse_output(package, output)
    assert (
        issues[0].message == "unconfigured build_depend on "
        "(Make sure you aren't missing "
        "COMPONENTS in find_package(catkin ...) "
        "in CMakeLists.txt) "
        "(I can't really tell if this applies for "
        "package.xml or CMakeLists.txt. Make sure to "
        "check both for this issue)"
    )

    output = "custom_pkg: CMakeLists.txt(5): error: include_directories() needs missing directory '/include'"
    issues = cltp.parse_output(package, output)
    assert (
        issues[0].message == "include_directories() needs missing directory '/include'"
    )


def test_catkin_lint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of catkin_lint."""
    cltp = setup_catkin_lint_tool_plugin()
    output = "invalid text"
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.parse_output(package, output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.catkin_lint_tool_plugin.subprocess.check_output")
def test_catkin_lint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means catkin_lint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    cltp = setup_catkin_lint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = cltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.catkin_lint_tool_plugin.subprocess.check_output")
def test_catkin_lint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means catkin_lint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cltp = setup_catkin_lint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["catkin"] = "catkin"
    issues = cltp.scan(package, "level")
    assert issues is None
