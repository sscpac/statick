"""Unit tests for the YAMLLint tool plugin."""
import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.yamllint_tool_plugin import YamllintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_yamllint_tool_plugin():
    """Construct and return an instance of the YAMLLint plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    yltp = YamllintToolPlugin()
    yltp.set_plugin_context(plugin_context)
    return yltp


def test_yamllint_tool_plugin_found():
    """Test that the plugin manager finds the YAMLLint plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "yamllint"
    assert any(plugin_info.plugin_object.get_name() == 'yamllint' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named Yamllint Tool Plugin
    assert any(plugin_info.name == 'yamllint Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))


def test_yamllint_tool_plugin_scan_valid():
    """Integration test: Make sure the yamllint output hasn't changed."""
    yltp = setup_yamllint_tool_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['yaml'] = [os.path.join(os.path.dirname(__file__),
                                    'valid_package', 'document-start.yaml')]
    issues = yltp.scan(package, 'level')
    assert len(issues) == 1


def test_yamllint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of yamllint."""
    yltp = setup_yamllint_tool_plugin()
    output = 'valid_package/document-start.yaml:1:1: [warning] missing document start "---" (document-start)'
    issues = yltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == 'valid_package/document-start.yaml'
    assert issues[0].line_number == '1'
    assert issues[0].tool == 'yamllint'
    assert issues[0].issue_type == 'document-start'
    assert issues[0].severity == '3'
    assert issues[0].message == 'missing document start "---"'


def test_yamllint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of yamllint."""
    yltp = setup_yamllint_tool_plugin()
    output = "invalid text"
    issues = yltp.parse_output(output)
    assert not issues
