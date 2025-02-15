"""Unit tests for the groovylint plugin."""
import argparse
import os
import subprocess
import sys

import mock
import pytest

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.groovylint import GroovyLintToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_groovylint_tool_plugin():
    """Initialize and return an instance of the groovylint plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )

    resources = Resources(
        [
            os.path.join(os.path.dirname(statick_tool.__file__), "plugins"),
            os.path.join(os.path.dirname(__file__), "valid_package"),
        ]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin = GroovyLintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_groovylint_tool_plugin_found():
    """Test that the plugin manager can find the groovylint plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "groovylint" for _, plugin in list(plugins.items())
    )


def test_groovylint_tool_plugin_scan_valid():
    """Integration test: Make sure the groovylint output hasn't changed."""
    plugin = setup_groovylint_tool_plugin()
    if not plugin.command_exists("npm-groovy-lint"):
        pytest.skip("Missing groovylint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["groovy_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Jenkinsfile"),
        os.path.join(os.path.dirname(__file__), "valid_package", "test.gradle"),
        os.path.join(os.path.dirname(__file__), "valid_package", "test.groovy"),
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_groovylint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the groovylint output hasn't changed."""
    plugin = setup_groovylint_tool_plugin()
    if not plugin.command_exists("npm-groovy-lint"):
        pytest.skip("Missing groovylint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["groovy_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test_errors.groovy")
    ]
    issues = plugin.scan(package, "level")
    # We expect to have unused variable error, a line too long warning, and a
    # string quote mark info statement.
    assert len(issues) == 3


def test_groovylint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of groovylint."""
    plugin = setup_groovylint_tool_plugin()
    output = '{"summary":{"totalFilesWithErrorsNumber":1,"totalFilesLinted":1,"totalFoundErrorNumber":0,"totalFoundWarningNumber":0,"totalFoundInfoNumber":1,"totalFoundNumber":1,"totalFixedNumber":0,"totalRemainingNumber":1,"totalFixedErrorNumber":0,"totalFixedWarningNumber":0,"totalFixedInfoNumber":0,"totalRemainingErrorNumber":0,"totalRemainingWarningNumber":0,"totalRemainingInfoNumber":1,"detectedRules":{"UnnecessaryGString":1},"fixedRules":{}},"linesNumber":4,"files":{"test_errors.groovy":{"errors":[{"id":0,"line":3,"rule":"UnnecessaryGString","severity":"info","msg":"The String \'Hello World!\' can be wrapped in single quotes instead of double quotes","fixable":true,"fixLabel":"Replace double quotes by single quotes","range":{"start":{"line":3,"character":9},"end":{"line":3,"character":21}}}]}}}'
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test_errors.groovy"
    assert issues[0].line_number == 3
    assert issues[0].tool == "groovylint"
    assert issues[0].issue_type == "UnnecessaryGString"
    assert issues[0].severity == 1
    assert (
        issues[0].message
        == "The String 'Hello World!' can be wrapped in single quotes instead of double quotes"
    )


def test_groovylint_tool_plugin_parse_invalid():
    """Verify that invalid output of groovylint is ignored."""
    plugin = setup_groovylint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


def test_groovylint_tool_plugin_parse_no_summary():
    """Test what happens when input has no summary.

    Expected result: no issues found
    """
    plugin = setup_groovylint_tool_plugin()
    output = '{"nothing_we_parse":{"totalFilesWithErrorsNumber":1}}'
    issues = plugin.parse_output([output])
    assert not issues


@mock.patch("statick_tool.plugins.tool.groovylint.subprocess.check_output")
def test_groovylint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means groovylint
    hit an error).

    Expected result: no issues found
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_groovylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["groovy_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.groovy")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.groovylint.subprocess.check_output")
def test_groovylint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means groovylint doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_groovylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["groovy_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.groovy")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
