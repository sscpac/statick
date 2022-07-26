"""Unit tests for the do nothing tool plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.package import Package
from statick_tool.plugins.tool.do_nothing_tool_plugin import DoNothingToolPlugin
from statick_tool.tool_plugin import ToolPlugin


def setup_do_nothing_tool_plugin():
    """Create and return an instance of the do nothing plugin."""
    plugin = DoNothingToolPlugin()
    return plugin


def test_do_nothing_tool_plugin_found():
    """Test that the plugin manager finds the do nothing tool plugin."""
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
    assert any(
        plugin_info.plugin_object.get_name() == "do_nothing"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    assert any(
        plugin_info.name == "Do Nothing Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_do_nothing_tool_plugin_get_file_types():
    """Integration test: Make sure the do_nothing output hasn't changed."""
    plugin = setup_do_nothing_tool_plugin()
    assert not plugin.get_file_types()


def test_do_nothing_tool_plugin_process_files():
    """Integration test: Make sure the do_nothing output hasn't changed."""
    plugin = setup_do_nothing_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "basic.py")
    ]
    output = plugin.process_files(package, "level", package["python_src"], [])
    assert not output


def test_do_nothing_tool_plugin_parse_output():
    """Verify that we can parse the normal output of do_nothing."""
    plugin = setup_do_nothing_tool_plugin()
    output = "would reformat /home/user/valid_package/basic.py"
    issues = plugin.parse_output([output])
    assert not issues
