"""Unit tests for cmakelint plugin."""
import argparse
import os
import subprocess

import mock
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.cmakelint_tool_plugin import CMakelintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_cmakelint_tool_plugin():
    """Create an instance of the cmakelint plugin."""
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
    cmltp = CMakelintToolPlugin()
    cmltp.set_plugin_context(plugin_context)
    return cmltp


def test_cmakelint_tool_plugin_found():
    """Test that the plugin manager finds the cmakelint plugin."""
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
    # Verify that a plugin's get_name() function returns "cmakelint"
    assert any(
        plugin_info.plugin_object.get_name() == "cmakelint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named cmakelint Tool Plugin
    assert any(
        plugin_info.name == "cmakelint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_cmakelint_tool_plugin_scan_valid():
    """Integration test: Make sure the cmakelint output hasn't changed."""
    cmltp = setup_cmakelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = cmltp.scan(package, "level")
    assert not issues

    package["cmake"] = "CMakeLists.txt"
    issues = cmltp.scan(package, "level")
    assert len(issues) == 1


def test_cmakelint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of cmakelint."""
    cmltp = setup_cmakelint_tool_plugin()
    output = "valid_package/CMakeLists.txt:1: Extra spaces between 'INVALID_FUNCTION' and its () [whitespace/extra]"
    issues = cmltp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/CMakeLists.txt"
    assert issues[0].line_number == "1"
    assert issues[0].tool == "cmakelint"
    assert issues[0].issue_type == "whitespace/extra"
    assert issues[0].severity == "3"
    assert issues[0].message == "Extra spaces between 'INVALID_FUNCTION' and its ()"

    output = "valid_package/CMakeLists.txt:1: fake warning [syntax]"
    issues = cmltp.parse_output(output)
    assert issues[0].severity == "5"


def test_cmakelint_tool_plugin_parse_invalid():
    """Verify that we don't parse invalid output of cmakelint."""
    cmltp = setup_cmakelint_tool_plugin()
    output = "invalid text"
    issues = cmltp.parse_output(output)
    assert not issues


def test_cmakelint_tool_plugin_nonexistent_file():
    """Check what happens when we try to scan a nonexistent file."""
    cmltp = setup_cmakelint_tool_plugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    package["cmake"] = "invalid.txt"
    issues = cmltp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.cmakelint_tool_plugin.subprocess.check_output")
def test_cmakelint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means cmakelint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    cmltp = setup_cmakelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["cmake"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "CMakeLists.txt")
    ]
    issues = cmltp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    issues = cmltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.cmakelint_tool_plugin.subprocess.check_output")
def test_cmakelint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means cmakelint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cmltp = setup_cmakelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["cmake"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "CMakeLists.txt")
    ]
    issues = cmltp.scan(package, "level")
    assert issues is None
