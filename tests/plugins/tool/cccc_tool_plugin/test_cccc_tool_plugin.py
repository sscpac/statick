"""Unit tests for the CCCC tool module."""

from __future__ import print_function

import argparse
import os
import shutil

import xmltodict
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.cccc_tool_plugin import CCCCToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_cccc_tool_plugin():
    """Create an instance of the CCCC plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_false", help="Show tool output")
    arg_parser.add_argument("--cccc-bin", dest="cccc_bin")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    ctp = CCCCToolPlugin()
    ctp.set_plugin_context(plugin_context)
    return ctp


def test_cccc_tool_plugin_found():
    """Test that the CCCC tool plugin is detected by the plugin system."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "cccc"
    assert any(plugin_info.plugin_object.get_name() == 'cccc' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named CCCC Tool Plugin
    assert any(plugin_info.name == 'CCCC Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))


# Has issues with not finding the cccc.opts config correctly.
# Plugin probably could use some touching up in this department
def test_cccc_tool_plugin_scan_valid():
    """Integration test: Make sure the CCCC output hasn't changed."""
    ctp = setup_cccc_tool_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['c_src'] = [os.path.join(os.path.dirname(__file__),
                                     'valid_package', 'example.cpp')]
    issues = ctp.scan(package, 'level')
    print('issues: {}'.format(issues))
    assert not issues


def test_cccc_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of CCCC."""
    ctp = setup_cccc_tool_plugin()

    # Copy the latest configuration file over.
    shutil.copyfile(ctp.plugin_context.resources.get_file("cccc.opt"),
                    os.path.join(os.path.dirname(__file__), 'cccc.opt'))
    config_file = ctp.plugin_context.resources.get_file('cccc.opt')

    output_file = os.path.join(os.path.dirname(__file__), 'valid_package', 'cccc.xml')
    with open(output_file) as f:
        output = xmltodict.parse(f.read())

    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['c_src'] = ['tmp/not_a_file.c']

    issues = ctp.parse_output(output, package, config_file)
    print('issues: {}'.format(issues))
    assert len(issues) == 1
    assert issues[0].filename == 'tmp/not_a_file.c'
    assert issues[0].line_number == 0
    assert issues[0].tool == 'cccc'
    assert issues[0].issue_type == 'warn'
    assert issues[0].severity == 3
    assert issues[0].message == 'Example1 - Fan in (concrete uses only) - value: 7.0, theshold: 6.0'


def test_cccc_tool_plugin_parse_invalid():
    """Verify that we don't return anything on bad input."""
    ctp = setup_cccc_tool_plugin()
    shutil.copyfile(ctp.plugin_context.resources.get_file("cccc.opt"),
                    os.path.join(os.path.dirname(__file__), 'cccc.opt'))
    config_file = ctp.plugin_context.resources.get_file('cccc.opt')
    output = "invalid text"
    package = {"c_src": "/tmp/not_a_file.c"}
    issues = ctp.parse_output(output, package, config_file)
    assert not issues
