"""Unit tests for the JSON reporting plugin."""
import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.reporting.json_reporting_plugin import JsonReportingPlugin
from statick_tool.reporting_plugin import ReportingPlugin
from statick_tool.resources import Resources

try:
    from tempfile import TemporaryDirectory
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from backports.tempfile import (  # pylint: disable=wrong-import-order
        TemporaryDirectory,
    )


def setup_json_reporting_plugin(file_path, use_plugin_context=True):
    """Create an instance of the file writer plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("output_directory")

    resources = Resources([os.path.join(os.path.dirname(__file__), "config")])
    config = Config(resources.get_file("config.yaml"))
    jrp = JsonReportingPlugin()
    if use_plugin_context:
        plugin_context = PluginContext(
            arg_parser.parse_args([file_path]), resources, config
        )
        jrp.set_plugin_context(plugin_context)
    return jrp


def test_json_reporting_plugin_found():
    """Test that the plugin manager finds the plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {
            "Reporting": ReportingPlugin,
        }
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "c"
    assert any(
        plugin_info.plugin_object.get_name() == "json"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
    )
    # While we're at it, verify that a plugin is named C Discovery Plugin
    assert any(
        plugin_info.name == "JSON Reporting Plugin"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
    )


def test_json_reporting_plugin_report_cert_reference():
    """Test the output of the reporting plugin where the issue has a CERT reference."""
    with TemporaryDirectory() as tmp_dir:
        jrp = setup_json_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", "1", "This is a test", "CERT")
            ]
        }
        _, success = jrp.report(package, issues, "level")
        assert success


def test_json_reporting_plugin_report_no_plugin_context():
    """Test the output of the reporting plugin without plugin context."""
    with TemporaryDirectory() as tmp_dir:
        jrp = setup_json_reporting_plugin(tmp_dir, False)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", "1", "This is a test", None)
            ]
        }
        _, success = jrp.report(package, issues, "level")
        assert not success


def test_json_reporting_plugin_report_fileexists():
    """Test the output of the reporting plugin if there's a file where the output dir
    should go."""
    with TemporaryDirectory() as tmp_dir:
        jrp = setup_json_reporting_plugin(tmp_dir)
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
        _, success = jrp.report(package, issues, "level")
        assert os.path.isfile(
            os.path.join(
                jrp.plugin_context.args.output_directory, "valid_package-level"
            )
        )
    assert not success


def test_json_reporting_plugin_write_output_no_plugin_context():
    """Test the write output method of the reporting plugin without plugin context."""
    with TemporaryDirectory() as tmp_dir:
        jrp = setup_json_reporting_plugin(tmp_dir, False)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        assert jrp.write_output(package, "level", "line")
        output_file = os.path.join(os.getcwd(), package.name + "-" + "level" + ".json")
        if os.path.exists(output_file):
            os.remove(output_file)
