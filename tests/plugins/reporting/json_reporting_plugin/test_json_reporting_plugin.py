"""Unit tests for the JSON reporting plugin."""
import argparse
import os
from importlib.metadata import entry_points
from tempfile import TemporaryDirectory

from statick_tool.config import Config
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.reporting.json import JsonReportingPlugin
from statick_tool.resources import Resources


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
    plugins = {}
    reporting_plugins = entry_points(group="statick_tool.plugins.reporting")
    for plugin_type in reporting_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "json" for _, plugin in list(plugins.items())
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
