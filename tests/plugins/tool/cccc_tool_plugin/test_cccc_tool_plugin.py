"""Unit tests for the CCCC tool module."""
import argparse
import os
import shutil

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
#from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.cccc_tool_plugin import CCCCToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_cccc_tool_plugin():
    """Create an instance of the cccc plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")

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
# def test_cccc_tool_plugin_scan_valid():
#     """Integration test: Make sure the cccc output hasn't changed."""
#     ctp = setup_cccc_tool_plugin()
#     package = Package('valid_package', os.path.join(os.path.dirname(__file__),
#                                                     'valid_package'))
#     package['c_src'] = [os.path.join(os.path.dirname(__file__),
#                                      'valid_package', 'example.c')]
#     issues = ctp.scan(package, 'level')
#     print(issues)
#     assert len(issues) == 1


def test_cccc_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of cccc."""
    ctp = setup_cccc_tool_plugin()

    # Copy the latest configuration file over.
    # shutil.copyfile(ctp.plugin_context.resources.get_file("cccc.opt"),
    #                 os.path.join(os.path.dirname(__file__), 'cccc.opt'))
    config_file = ctp.plugin_context.resources.get_file('cccc.opt')

    # output = "<?xml version='1.0' encoding='utf-8'?>]\n\
    # <!--Report on software metrics-->\n\
    # <CCCC_Project>\n\
    # <procedural_summary>\n\
    # <module>\n\
    # <name>ExampleTalker</name>\n\
    # <lines_of_code value='56' level='0' />\n\
    # <McCabes_cyclomatic_complexity value='5' level='0' />\n\
    # <lines_of_comment value='9' level='0' />\n\
    # <lines_of_code_per_line_of_comment value='6.222' level='0' />\n\
    # <McCabes_cyclomatic_complexity_per_line_of_comment value='0.556' level='0' />\n\
    # </module>\n\
    # </procedural_summary>\n\
    # </CCCC_Project>"
    package = {"c_src": "/tmp/not_a_file.c"}

    issues = ctp.parse_output(package, config_file)
    print('issues: {}'.format(issues))
    assert len(issues) == 1
    assert issues[0].filename == 'tmp/not_a_file.c'
    assert issues[0].line_number == '1'
    assert issues[0].tool == 'cccc'
    assert issues[0].issue_type == 'B404'
    assert issues[0].severity == '5'
    assert issues[0].message == "Consider possible security implications associated with subprocess module."


def test_cccc_tool_plugin_parse_invalid():
    """Verify that we don't return anything on bad input."""
    ctp = setup_cccc_tool_plugin()
    output = "invalid text"
    package = {"c_src": "/tmp/not_a_file.c"}
    issues = ctp.parse_output(package, output)
    assert not issues
