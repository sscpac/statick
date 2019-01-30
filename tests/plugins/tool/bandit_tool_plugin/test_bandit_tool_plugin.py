"""Unit tests for the bandit tool module."""
import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.bandit_tool_plugin import BanditToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_bandit_tool_plugin():
    """Create an instance of the bandit plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")
    arg_parser.add_argument("--bandit-bin", dest="bandit_bin")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    btp = BanditToolPlugin()
    btp.set_plugin_context(plugin_context)
    return btp


def test_bandit_tool_plugin_found():
    """Test that the bandit tool plugin is detected by the plugin system."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "bandit"
    assert any(plugin_info.plugin_object.get_name() == 'bandit' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named Bandit Tool Plugin
    assert any(plugin_info.name == 'Bandit Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))


def test_bandit_tool_plugin_scan_valid():
    """Integration test: Make sure the bandit output hasn't changed."""
    btp = setup_bandit_tool_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['python_src'] = [os.path.join(os.path.dirname(__file__),
                                          'valid_package', 'b404.py')]
    issues = btp.scan(package, 'level')
    assert len(issues) == 1


def test_bandit_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of bandit."""
    btp = setup_bandit_tool_plugin()
    output = ["filename,test_name,test_id,issue_severity,issue_confidence,issue_text,line_number,line_range,more_info",
              "valid_package/b404.py,blacklist,B404,LOW,HIGH,Consider possible security implications associated with subprocess module.,1,[1],https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess"]
    issues = btp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == 'valid_package/b404.py'
    assert issues[0].line_number == '1'
    assert issues[0].tool == 'bandit'
    assert issues[0].issue_type == 'B404'
    assert issues[0].severity == '5'
    assert issues[0].message == "Consider possible security implications associated with subprocess module."


def test_bandit_tool_plugin_parse_invalid():
    """Verify that we don't return anything on bad input."""
    btp = setup_bandit_tool_plugin()
    output = "invalid text"
    issues = btp.parse_output(output)
    assert not issues
