"""Unit tests for the isort plugin."""
import argparse
import os
import sys

import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.isort_tool_plugin import IsortToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_isort_tool_plugin():
    """Create and return an instance of the Isort plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    itp = IsortToolPlugin()
    itp.set_plugin_context(plugin_context)
    return itp


def test_isort_tool_plugin_found():
    """Test that the plugin manager can find the Isort plugin."""
    if sys.version_info.major == 3 and sys.version_info.minor < 6:
        pytest.skip("isort is only available for Python 3.6+, unable to test")
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
    # Verify that a plugin's get_name() function returns "isort"
    assert any(
        plugin_info.plugin_object.get_name() == "isort"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Isort Tool Plugin
    assert any(
        plugin_info.name == "Isort Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_isort_tool_plugin_scan_valid():
    """Integration test: Make sure the isort output hasn't changed."""
    if sys.version_info.major == 3 and sys.version_info.minor < 6:
        pytest.skip("isort is only available for Python 3.6+, unable to test")
    itp = setup_isort_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "sample.py")
    ]
    issues = itp.scan(package, "level")
    assert len(issues) == 1


def test_isort_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of isort."""
    itp = setup_isort_tool_plugin()
    total_output = []
    output = "/tmp/x.py"
    total_output.append(output)
    output = "/tmp/y.py"
    total_output.append(output)
    issues = itp.parse_output(total_output)
    assert len(issues) == 2
    assert issues[0].filename == "/tmp/x.py"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "isort"
    assert issues[0].issue_type == "formatting"
    assert issues[0].severity == "3"
    assert issues[0].message == "Imports are incorrectly sorted and/or formatted."
    assert issues[1].filename == "/tmp/y.py"
