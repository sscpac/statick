"""Unit tests for the do nothing tool plugin."""
import os
import sys

import statick_tool
from statick_tool.package import Package
from statick_tool.plugins.tool.do_nothing import DoNothingToolPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_do_nothing_tool_plugin():
    """Create and return an instance of the do nothing plugin."""
    plugin = DoNothingToolPlugin()
    return plugin


def test_do_nothing_tool_plugin_found():
    """Test that the plugin manager finds the do nothing tool plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "do_nothing" for _, plugin in list(plugins.items())
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
