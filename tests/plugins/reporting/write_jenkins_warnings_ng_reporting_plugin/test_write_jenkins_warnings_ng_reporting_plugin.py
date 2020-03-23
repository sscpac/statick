"""Unit tests for the file writing reporting plugin."""
import argparse
import json
import os
import re

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.reporting.write_jenkins_warnings_ng_reporting_plugin import (
    WriteJenkinsWarningsNGReportingPlugin,
)
from statick_tool.reporting_plugin import ReportingPlugin
from statick_tool.resources import Resources

try:
    from tempfile import TemporaryDirectory
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from backports.tempfile import (
        TemporaryDirectory,
    )  # pylint: disable=wrong-import-order

output_regex = r"^{\"(.*)\": \"(.*)\", \"(.*)\": \"(.*)\", \"(.*)\": (\d+), \"(.*)\": \"(.*)\", \"(.*)\": \"(.*)\", \"(.*)\": \"(.*)\"}"


def setup_write_jenkins_warnings_ng_reporting_plugin(
    file_path, use_plugin_context=True
):
    """Create an instance of the file writer plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("output_directory")
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )

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
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {"Reporting": ReportingPlugin,}
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "c"
    assert any(
        plugin_info.plugin_object.get_name() == "write_jenkins_warnings_ng"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
    )
    # While we're at it, verify that a plugin is named C Discovery Plugin
    assert any(
        plugin_info.name == "Write Jenkins Warnings NG Reporting Plugin"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
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
                Issue("test.txt", 1, "tool_a", "type", "1", "This is a test", None)
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
                Issue("test.txt", 1, "tool_a", "type", "1", "This is a test", None)
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
                Issue("test.txt", 1, "tool_a", "type", "0", "This is a test", None),
                Issue(
                    "test.txt",
                    1,
                    "tool_a",
                    "type",
                    "invalid-severity",
                    "This is a test",
                    None,
                ),
                Issue("test.txt", 1, "tool_a", "type", "1", "This is a test", None),
                Issue("test.txt", 1, "tool_a", "type", 3, "This is a test", None),
                Issue("test.txt", 1, "tool_a", "type", "5", "This is a test", None),
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
    """Test the output of the reporting plugin if there's a file where the output dir should go."""
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
