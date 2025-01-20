"""Unit tests for the dockerfilelint plugin."""
import argparse
import os
import subprocess
import sys

import mock
import pytest
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources

import statick_tool
from statick_tool.plugins.tool.dockerfilelint import DockerfileLintToolPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_dockerfilelint_tool_plugin(package="valid_package"):
    """Initialize and return an instance of the dockerfilelint plugin."""
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
            os.path.join(os.path.dirname(__file__), package),
        ]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin = DockerfileLintToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_dockerfilelint_tool_plugin_found():
    """Test that the plugin manager can find the dockerfilelint plugin."""
    tool_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        tool_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "dockerfilelint" for _, plugin in list(tool_plugins.items())
    )


def test_dockerfilelint_tool_plugin_scan_valid():
    """Integration test: Make sure the dockerfilelint output hasn't changed."""
    plugin = setup_dockerfilelint_tool_plugin()
    if not plugin.command_exists("dockerfilelint"):
        pytest.skip("Missing dockerfilelint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile.noissues")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_dockerfilelint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the dockerfilelint output hasn't changed."""
    plugin = setup_dockerfilelint_tool_plugin()
    if not plugin.command_exists("dockerfilelint"):
        pytest.skip("Missing dockerfilelint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    # We expect a base image latest tag, extra arguments and expose only container port issues
    assert len(issues) == 3


def test_dockerfilelint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of dockerfilelint."""
    plugin = setup_dockerfilelint_tool_plugin()
    output = '{"files":[{"file":"Dockerfile","issues_count":1,"issues":[{"line":"2","content":"USER hello world","category":"Possible Bug","title":"Extra Arguments","description":"This command has extra arguments and will be ignored."}]}],"totalIssues":1}'
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "Dockerfile"
    assert issues[0].line_number == "2"
    assert issues[0].tool == "dockerfilelint"
    assert issues[0].issue_type == "Extra Arguments"
    assert issues[0].severity == "3"
    assert issues[0].message == "This command has extra arguments and will be ignored."


def test_dockerfilelint_tool_plugin_parse_invalid():
    """Verify that invalid output of dockerfilelint is ignored."""
    plugin = setup_dockerfilelint_tool_plugin()
    output = "invalid text\n"
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "EXCEPTION"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "dockerfilelint"
    assert issues[0].issue_type == "ValueError"
    assert issues[0].severity == "5"
    assert issues[0].message == "Expecting value: line 1 column 1 (char 0), on line: invalid text"


def test_dockerfilelint_tool_plugin_scan_invalid_rc_file():
    """Integration test: Make sure the dockerfilelint output hasn't changed."""
    plugin = setup_dockerfilelint_tool_plugin(package="invalidrc_package")
    if not plugin.command_exists("dockerfilelint"):
        pytest.skip("Missing dockerfilelint executable.")
    package = Package(
        "invalidrc_package", os.path.join(os.path.dirname(__file__), "invalidrc_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "invalidrc_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    # Expecting 1 issue for each of the following lines:
    # /usr/local/lib/node_modules/dockerfilelint/lib/messages.js:14
    # if (name in rules) {
    #          ^
    # TypeError: Cannot use 'in' operator to search for 'latest_tag' in null
    # at Object.build (/usr/local/lib/node_modules/dockerfilelint/lib/messages.js:14:14)
    # at /usr/local/lib/node_modules/dockerfilelint/lib/index.js:150:31
    # at Array.forEach (<anonymous>)
    # at runLine (/usr/local/lib/node_modules/dockerfilelint/lib/index.js:149:37)
    # at Object.module.exports.run (/usr/local/lib/node_modules/dockerfilelint/lib/index.js:62:18)
    # at processContent (/usr/local/lib/node_modules/dockerfilelint/bin/dockerfilelint:92:50)
    # at /usr/local/lib/node_modules/dockerfilelint/bin/dockerfilelint:86:3
    # at Array.forEach (<anonymous>)
    # at Object.<anonymous> (/usr/local/lib/node_modules/dockerfilelint/bin/dockerfilelint:65:8)
    # at Module._compile (internal/modules/cjs/loader.js:1063:30)
    assert len(issues) == 15
    assert issues[2].filename == "EXCEPTION"
    assert issues[2].line_number == "0"
    assert issues[2].tool == "dockerfilelint"
    assert issues[2].issue_type == "ValueError"
    assert issues[2].severity == "5"
    assert issues[2].message == "Expecting value: line 1 column 14 (char 13), on line:              ^"


@mock.patch(
    "statick_tool.plugins.tool.dockerfilelint.subprocess.check_output"
)
def test_dockerfilelint_tool_plugin_scan_calledprocesserror(
    mock_subprocess_check_output,
):
    """
    Test what happens when a CalledProcessError is raised (usually means dockerfilelint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_dockerfilelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert len(issues) == 1
    assert issues[0].filename == "EXCEPTION"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "dockerfilelint"
    assert issues[0].issue_type == "ValueError"
    assert issues[0].severity == "5"
    assert issues[0].message == "Expecting value: line 1 column 1 (char 0), on line: mocked error"


@mock.patch(
    "statick_tool.plugins.tool.dockerfilelint.subprocess.check_output"
)
def test_dockerfilelint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means dockerfilelint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_dockerfilelint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
