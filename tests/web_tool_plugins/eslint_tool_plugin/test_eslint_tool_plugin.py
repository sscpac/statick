"""Unit tests for the eslint plugin."""
import argparse
import os
import subprocess

import mock
import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.eslint_tool_plugin import ESLintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_eslint_tool_plugin():
    """Initialize and return an instance of the eslint plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_false", help="Show tool output")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__), 'plugins'),
                           os.path.join(os.path.dirname(__file__), 'valid_package')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin = ESLintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_eslint_tool_plugin_found():
    """Test that the plugin manager can find the eslint plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Tool": ToolPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "eslint"
    assert any(plugin_info.plugin_object.get_name() == 'eslint' for
               plugin_info in manager.getPluginsOfCategory("Tool"))
    # While we're at it, verify that a plugin is named ESLint Tool Plugin
    assert any(plugin_info.name == 'ESLint Tool Plugin' for
               plugin_info in manager.getPluginsOfCategory("Tool"))


def test_eslint_tool_plugin_scan_valid():
    """Integration test: Make sure the eslint output hasn't changed."""
    plugin = setup_eslint_tool_plugin()
    if not plugin.command_exists("eslint"):
        pytest.skip("Missing eslint executable.")
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['javascript_src'] = [os.path.join(os.path.dirname(__file__),
                                              'valid_package', 'test_no_issues.js')]
    issues = plugin.scan(package, 'level')
    assert not issues


def test_eslint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the eslint output hasn't changed."""
    plugin = setup_eslint_tool_plugin()
    if not plugin.command_exists("eslint"):
        pytest.skip("Missing eslint executable.")
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['html_src'] = [os.path.join(os.path.dirname(__file__),
                                        'valid_package', 'test.html')]
    package['javascript_src'] = [os.path.join(os.path.dirname(__file__),
                                              'valid_package', 'test.js')]
    issues = plugin.scan(package, 'level')
    # We expect to have camelcase warnings and no-unused-var errors.
    assert len(issues) == 4


def test_eslint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of eslint."""
    plugin = setup_eslint_tool_plugin()
    output = 'test.js:1:13: Strings must use singlequote. [Error/quotes]'
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == 'test.js'
    assert issues[0].line_number == '1'
    assert issues[0].tool == 'eslint'
    assert issues[0].issue_type == 'quotes'
    assert issues[0].severity == 5
    assert issues[0].message == 'Strings must use singlequote.'


def test_eslint_tool_plugin_parse_invalid():
    """Verify that invalid output of eslint is ignored."""
    plugin = setup_eslint_tool_plugin()
    output = 'invalid text'
    issues = plugin.parse_output(output)
    assert not issues


@mock.patch('statick_tool.plugins.tool.eslint_tool_plugin.subprocess.check_output')
def test_eslint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means eslint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(0, '', output="mocked error")
    plugin = setup_eslint_tool_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['html_src'] = [os.path.join(os.path.dirname(__file__),
                                        'valid_package', 'test.html')]
    package['javascript_src'] = [os.path.join(os.path.dirname(__file__),
                                              'valid_package', 'test.js')]
    issues = plugin.scan(package, 'level')
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(2, '', output="mocked error")
    issues = plugin.scan(package, 'level')
    assert not issues


@mock.patch('statick_tool.plugins.tool.eslint_tool_plugin.subprocess.check_output')
def test_eslint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means eslint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError('mocked error')
    plugin = setup_eslint_tool_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    package['html_src'] = [os.path.join(os.path.dirname(__file__),
                                        'valid_package', 'test.html')]
    package['javascript_src'] = [os.path.join(os.path.dirname(__file__),
                                              'valid_package', 'test.js')]
    issues = plugin.scan(package, 'level')
    assert issues is None
