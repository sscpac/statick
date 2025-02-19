"""Unit tests for the file writing reporting plugin."""

import argparse
import json
import os
import re
import sys

import statick_tool
from statick_tool.config import Config
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.reporting.write_jenkins_warnings_ng import (
    WriteJenkinsWarningsNGReportingPlugin,
)
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from tempfile import TemporaryDirectory

output_regex = r"^{\"(.*)\": \"(.*)\", \"(.*)\": \"(.*)\", \"(.*)\": (\d+), \"(.*)\": \"(.*)\", \"(.*)\": \"(.*)\", \"(.*)\": \"(.*)\"}"


def setup_write_jenkins_warnings_ng_reporting_plugin(
    file_path, use_plugin_context=True
):
    """Create an instance of the file writer plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("output_directory")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    wfrp = WriteJenkinsWarningsNGReportingPlugin()
    if use_plugin_context:
        plugin_context = PluginContext(
            arg_parser.parse_args([file_path]), resources, config
        )
        wfrp.set_plugin_context(plugin_context)
    return wfrp


def test_write_jenkins_warnings_ng_reporting_plugin_found():
    """Test that the plugin manager finds the file writing plugin."""
    plugins = {}
    reporting_plugins = entry_points(group="statick_tool.plugins.reporting")
    for plugin_type in reporting_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "write_jenkins_warnings_ng" for _, plugin in list(plugins.items())
    )


def test_write_jenkins_warnings_ng_reporting_plugin_report_no_plugin_context():
    """Test the output of the reporting plugin without plugin context."""
    with TemporaryDirectory() as tmp_dir:
        wfrp = setup_write_jenkins_warnings_ng_reporting_plugin(tmp_dir, False)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", None)
            ]
        }
        _, success = wfrp.report(package, issues, "level")
        assert not success


def test_write_jenkins_warnings_ng_reporting_plugin_report_nocert():
    """Test the output of the reporting plugin without a CERT reference."""
    with TemporaryDirectory() as tmp_dir:
        wfrp = setup_write_jenkins_warnings_ng_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", None)
            ]
        }
        _, success = wfrp.report(package, issues, "level")
        assert success
        with open(
            os.path.join(
                tmp_dir, "valid_package-level", "valid_package-level.json.statick"
            )
        ) as outfile:
            line = outfile.readline().strip()
    expected_dict = {
        "fileName": "test.txt",
        "severity": "NORMAL",
        "lineStart": 1,
        "message": "This is a test",
        "category": "tool_a",
        "type": "type",
    }
    output_dict = json.loads(line)
    assert output_dict == expected_dict
    assert re.match(output_regex, line)
    assert (
        line
        == '{"category": "tool_a", "fileName": "test.txt", "lineStart": 1, "message": "This is a test", "severity": "NORMAL", "type": "type"}'
    )
    assert line == json.dumps(expected_dict, sort_keys=True)


def test_write_jenkins_warnings_ng_reporting_plugin_report_severities():
    """Test the output of the reporting plugin with different severities."""
    with TemporaryDirectory() as tmp_dir:
        wfrp = setup_write_jenkins_warnings_ng_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", 0, "This is a test", None),
                Issue(
                    "test.txt",
                    1,
                    "tool_a",
                    "type",
                    "invalid-severity",
                    "This is a test",
                    None,
                ),
                Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", None),
                Issue("test.txt", 1, "tool_a", "type", 3, "This is a test", None),
                Issue("test.txt", 1, "tool_a", "type", 5, "This is a test", None),
            ]
        }
        _, success = wfrp.report(package, issues, "level")
        assert success
        with open(
            os.path.join(
                tmp_dir, "valid_package-level", "valid_package-level.json.statick"
            )
        ) as outfile:
            for line in outfile:
                line = line.strip()
                assert re.match(output_regex, line)
    expected_dict = {
        "fileName": "test.txt",
        "severity": "ERROR",
        "lineStart": 1,
        "message": "This is a test",
        "category": "tool_a",
        "type": "type",
    }
    output_dict = json.loads(line)
    assert output_dict == expected_dict
    assert re.match(output_regex, line)
    assert (
        line
        == '{"category": "tool_a", "fileName": "test.txt", "lineStart": 1, "message": "This is a test", "severity": "ERROR", "type": "type"}'
    )
    assert line == json.dumps(expected_dict, sort_keys=True)


def test_write_jenkins_warnings_ng_reporting_plugin_report_fileexists():
    """Test the output of the reporting plugin if there's a file where the output dir
    should go."""
    with TemporaryDirectory() as tmp_dir:
        wfrp = setup_write_jenkins_warnings_ng_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        # Makes a file where we expect a dir
        open(os.path.join(tmp_dir, package.name + "-" + "level"), "w").close()
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", None)
            ]
        }
        _, success = wfrp.report(package, issues, "level")
        assert os.path.isfile(
            os.path.join(
                wfrp.plugin_context.args.output_directory, "valid_package-level"
            )
        )
    assert not success
