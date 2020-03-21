"""Unit tests for the Pyflakes plugin."""
import argparse
import os
import subprocess

import mock
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.pyflakes_tool_plugin import PyflakesToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_pyflakes_tool_plugin():
    """Initialize and return a Pyflakes plugin."""
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
    pftp = PyflakesToolPlugin()
    pftp.set_plugin_context(plugin_context)
    return pftp


def test_pyflakes_tool_plugin_found():
    """Test that the plugin manager can find the Pyflakes plugin."""
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
    # Verify that a plugin's get_name() function returns "pyflakes"
    assert any(
        plugin_info.plugin_object.get_name() == "pyflakes"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Pyflakes Tool Plugin
    assert any(
        plugin_info.name == "Pyflakes Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_pyflakes_tool_plugin_scan_valid():
    """Integration test: Make sure the pyflakes output hasn't changed."""
    pftp = setup_pyflakes_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pyflakes_test.py")
    ]
    issues = pftp.scan(package, "level")
    assert len(issues) == 1


def test_pyflakes_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of pyflakes."""
    pftp = setup_pyflakes_tool_plugin()
    output = (
        "pyflakes_test.py:39:34: invalid syntax\nprint 'No files in %s' "
        "% (source_dir)"
    )
    issues = pftp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "pyflakes_test.py"
    assert issues[0].line_number == "39"
    assert issues[0].tool == "pyflakes"
    assert issues[0].issue_type == "invalid syntax"
    assert issues[0].severity == "5"


def test_pyflakes_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of pyflakes."""
    pftp = setup_pyflakes_tool_plugin()
    output = "invalid text"
    issues = pftp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.pyflakes_tool_plugin.subprocess.check_output")
def test_pyflakes_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means pyflakes hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    pltp = setup_pyflakes_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pyflakes_test.py")
    ]
    issues = pltp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = pltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.pyflakes_tool_plugin.subprocess.check_output")
def test_pyflakes_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means pyflakes doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    pltp = setup_pyflakes_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pyflakes_test.py")
    ]
    issues = pltp.scan(package, "level")
    assert issues is None
