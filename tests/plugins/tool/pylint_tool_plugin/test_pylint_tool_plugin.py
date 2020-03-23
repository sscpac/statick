"""Unit tests for the Pylint tool plugin."""
import argparse
import os
import subprocess

import mock
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.pylint_tool_plugin import PylintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_pylint_tool_plugin():
    """Construct and return an instance of the Pylint plugin."""
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
    pltp = PylintToolPlugin()
    pltp.set_plugin_context(plugin_context)
    return pltp


def test_pylint_tool_plugin_found():
    """Test that the plugin manager finds the Pylint plugin."""
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
    # Verify that a plugin's get_name() function returns "pylint"
    assert any(
        plugin_info.plugin_object.get_name() == "pylint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Pylint Tool Plugin
    assert any(
        plugin_info.name == "Pylint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_pylint_tool_plugin_scan_valid():
    """Integration test: Make sure the pylint output hasn't changed."""
    pltp = setup_pylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "basic.py")
    ]
    issues = pltp.scan(package, "level")
    # We expect to have missing docstring and unused import warnings.
    assert len(issues) == 2


def test_pylint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of pylint."""
    pltp = setup_pylint_tool_plugin()
    output = "basic.py:1: [W0611(unused-import), ] Unused import subprocess"
    issues = pltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "basic.py"
    assert issues[0].line_number == "1"
    assert issues[0].tool == "pylint"
    assert issues[0].issue_type == "W0611(unused-import)"
    assert issues[0].severity == "5"
    assert issues[0].message == "Unused import subprocess"

    output = "basic.py:1: [W0611(unused-import)] Unused import subprocess"
    issues = pltp.parse_output([output])
    assert issues[0].message == "Unused import subprocess"

    output = "basic.py:1: [W0611(unused-import), not-empty] Unused import subprocess"
    issues = pltp.parse_output([output])
    assert issues[0].message == "not-empty: Unused import subprocess"


def test_pylint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of pylint."""
    pltp = setup_pylint_tool_plugin()
    output = "invalid text"
    issues = pltp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.pylint_tool_plugin.subprocess.check_output")
def test_pylint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means pylint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    pltp = setup_pylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pylint_test.py")
    ]
    issues = pltp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = pltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.pylint_tool_plugin.subprocess.check_output")
def test_pylint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means pylint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    pltp = setup_pylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pylint_test.py")
    ]
    issues = pltp.scan(package, "level")
    assert issues is None
