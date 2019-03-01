"""Unit tests for the clang-tidy plugin."""
import argparse
import os
import shutil
import subprocess
import tempfile

import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.clang_tidy_tool_plugin import \
    ClangTidyToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_clang_tidy_tool_plugin():
    """Initialize and return an instance of the clang-tidy plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")
    arg_parser.add_argument("--clang-tidy-bin", dest="clang_tidy_bin")
    arg_parser.add_argument('--mapping-file-suffix', dest="mapping_file_suffix",
                            type=str)

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    cttp = ClangTidyToolPlugin()
    cttp.set_plugin_context(plugin_context)
    return cttp


def test_clang_tidy_tool_plugin_found():
    """Test that the plugin manager can find the clang-tidy plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "clang_tidy"
    assert any(plugin_info.plugin_object.get_name() == 'clang-tidy' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named ClangTidy Tool Plugin
    assert any(plugin_info.name == 'clang-tidy Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))


def test_clang_tidy_tool_plugin_scan_valid(monkeypatch):
    """Integration test: Make sure the clang_tidy output hasn't changed."""
    cttp = setup_clang_tidy_tool_plugin()
    if not cttp.command_exists('cmake'):
        pytest.skip("Can't find CMake, unable to test clang_tidy plugin")
    elif not cttp.command_exists('clang-tidy'):
        pytest.skip("Can't find clang-tidy, unable to test clang_tidy plugin")
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))

    # Need to actually run CMake to generate compile_commands.json
    bin_dir = tempfile.mkdtemp()
    monkeypatch.chdir(bin_dir)
    try:
        subprocess.check_output(["cmake", os.path.join(os.path.dirname(__file__), 'valid_package'),
                                 "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                                 "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                                 "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=" + bin_dir],
                                universal_newlines=True)
    except subprocess.CalledProcessError as ex:
        print("Problem running CMake! Returncode = {}".
              format(str(ex.returncode)))
        print("{}".format(ex.output))
        pytest.fail("Failed running CMake")

    package['make_targets'] = []
    package['make_targets'].append({})
    package['make_targets'][0]['src'] = [os.path.join(os.path.dirname(__file__),
                                                      'valid_package', 'test.c')]
    package['bin_dir'] = bin_dir
    package['src_dir'] = os.path.join(os.path.dirname(__file__), 'valid_package')
    issues = cttp.scan(package, 'level')
    assert len(issues) == 1
    assert issues[0].filename == os.path.join(os.path.dirname(__file__), 'valid_package', 'test.c')
    assert issues[0].line_number == '6'
    assert issues[0].tool == 'clang-tidy'
    assert issues[0].issue_type == 'warning/clang-analyzer-deadcode.DeadStores'
    assert issues[0].severity == '3'
    assert issues[0].message == "Value stored to 'si' is never read"
    shutil.rmtree(bin_dir)


def test_clang_tidy_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of clang_tidy."""
    cttp = setup_clang_tidy_tool_plugin()
    output = "valid_package/test.c:6:5: warning: Value stored to 'si' is never read [clang-analyzer-deadcode.DeadStores]"
    issues = cttp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == os.path.join('valid_package', 'test.c')
    assert issues[0].line_number == '6'
    assert issues[0].tool == 'clang-tidy'
    assert issues[0].issue_type == 'warning/clang-analyzer-deadcode.DeadStores'
    assert issues[0].severity == '3'
    assert issues[0].message == "Value stored to 'si' is never read"


def test_clang_tidy_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of clang_tidy."""
    cttp = setup_clang_tidy_tool_plugin()
    output = "invalid text"
    issues = cttp.parse_output(output)
    assert not issues
