"""Unit tests for the chktex plugin."""
import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.chktex_tool_plugin.chktex_tool_plugin import \
    ChktexToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_chktex_tool_plugin():
    """Initialize and return an instance of the chktex plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    ctp = ChktexToolPlugin()
    ctp.set_plugin_context(plugin_context)
    return ctp


def test_chktex_tool_plugin_found():
    """Test that the plugin manager can find the chktex plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "chktex"
    assert any(plugin_info.plugin_object.get_name() == 'chktex' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named Chktex Tool Plugin
    assert any(plugin_info.name == 'Chktex Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
