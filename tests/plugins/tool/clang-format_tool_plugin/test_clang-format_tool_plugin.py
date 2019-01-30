"""Unit tests for the clang-format plugin."""
import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.clang_format_tool_plugin import \
    ClangFormatToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_clang_format_tool_plugin():
    """Initialize and return an instance of the clang-format plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")
    arg_parser.add_argument("--clang-format-bin", dest="clang_format_bin")
    arg_parser.add_argument("--clang-format-raise-exception",
                            dest="clang_format_raise_exception",
                            action="store_true", default=True)

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    cftp = ClangFormatToolPlugin()
    cftp.set_plugin_context(plugin_context)
    return cftp


def test_clang_format_tool_plugin_found():
    """Test that the plugin manager can find the clang-format plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "clang_format"
    assert any(plugin_info.plugin_object.get_name() == 'clang-format' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named ClangFormat Tool Plugin
    assert any(plugin_info.name == 'clang-format Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))


# Has issues with not finding the clang-format config correctly. Plugin probably could
# use some touching up in this department
# def test_clang_format_tool_plugin_scan_valid():
#    """Integration test: Make sure the clang_format output hasn't changed."""
#    cftp = setup_clang_format_tool_plugin()
#    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
#                                                    'valid_package'))
#
#    # Copy the latest clang_format over
#    shutil.copyfile(cftp.plugin_context.resources.get_file("_clang-format"),
#                    os.path.join(os.path.dirname(__file__), '_clang-format'))
#    package['make_targets'] = []
#    package['make_targets'].append({})
#    package['make_targets'][0]['src'] = [os.path.join(os.path.dirname(__file__),
#                                                      'valid_package', 'indents.c')]
#    issues = cftp.scan(package, 'level')
#    assert len(issues) == 1
#
#
def test_clang_format_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of clang_format."""
    cftp = setup_clang_format_tool_plugin()
    output = "valid_package/indents.c\n\
<?xml version='1.0'?>\n\
<replacements xml:space='preserve' incomplete_format='false'>\n\
<replacement offset='12' length='1'>&#10;  </replacement>\n\
</replacements>"
    issues = cftp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == 'valid_package/indents.c'
    assert issues[0].line_number == '0'
    assert issues[0].tool == 'clang-format'
    assert issues[0].issue_type == 'format'
    assert issues[0].severity == '1'
    assert issues[0].message == "1 replacements"


def test_clang_format_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of clang_format."""
    cftp = setup_clang_format_tool_plugin()
    output = "invalid text"
    issues = cftp.parse_output(output)
    assert not issues
