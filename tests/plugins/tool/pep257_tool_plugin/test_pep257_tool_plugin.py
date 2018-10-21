import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.pep257_tool_plugin import Pep257ToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_pep257_tool_plugin():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                           'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    p257tp = Pep257ToolPlugin()
    p257tp.set_plugin_context(plugin_context)
    return p257tp


def test_pep257_tool_plugin_found():
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "pep257"
    assert(any(plugin_info.plugin_object.get_name() == 'pep257' for
               plugin_info in manager.getPluginsOfCategory("Tool")))
    # While we're at it, verify that a plugin is named Pep257 Tool Plugin
    assert(any(plugin_info.name == 'PEP257 Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool")))


def test_pep257_tool_plugin_scan_valid():
    '''Integration test: Make sure the pep257 output hasn't changed'''
    p257tp = setup_pep257_tool_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['python_src'] = [os.path.join(os.path.dirname(__file__),
                             'valid_package', 'd103.py')]
    issues = p257tp.scan(package, 'level')
    assert(len(issues) == 1)


def test_pep257_tool_plugin_parse_valid():
    '''Verify that we can parse the normal output of pep257'''
    p257tp = setup_pep257_tool_plugin()
    output = "valid_package/d103.py:3 in public function `some_method`:\n\
 D103: Missing docstring in public function"
    issues = p257tp.parse_output([output])
    assert(len(issues) == 1)
    assert(issues[0].filename == 'valid_package/d103.py')
    assert(issues[0].line_number == '3')
    assert(issues[0].tool == 'pep257')
    assert(issues[0].issue_type == 'D103')
    assert(issues[0].severity == '5')
    assert(issues[0].message == "Missing docstring in public function")


def test_pep257_tool_plugin_parse_invalid():
    '''Verify that we can parse the normal output of pep257'''
    p257tp = setup_pep257_tool_plugin()
    output = "invalid text"
    issues = p257tp.parse_output(output)
    assert(not issues)
