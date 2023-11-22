"""Unit tests for the JSON reporting plugin."""
import argparse
import json
import os
import sys

from statick_tool.config import Config
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.reporting.code_climate import CodeClimateReportingPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

try:
    from tempfile import TemporaryDirectory
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from backports.tempfile import (  # pylint: disable=wrong-import-order
        TemporaryDirectory,
    )


def setup_code_climate_reporting_plugin(
    file_path,
    use_plugin_context=True,
    config_filename="config.yaml",
    use_output_directory=True,
):
    """Create an instance of the file writer plugin."""
    arg_parser = argparse.ArgumentParser()
    if use_output_directory:
        arg_parser.add_argument("output_directory")
    else:
        arg_parser.add_argument("dummy")

    resources = Resources([os.path.join(os.path.dirname(__file__), "config")])
    config = Config(resources.get_file(config_filename))
    plugin = CodeClimateReportingPlugin()
    if use_plugin_context:
        plugin_context = PluginContext(
            arg_parser.parse_args([file_path]), resources, config
        )
        plugin.set_plugin_context(plugin_context)
    return plugin


def test_code_climate_reporting_plugin_found():
    """Test that the plugin manager finds the plugin."""
    plugins = {}
    reporting_plugins = entry_points(group="statick_tool.plugins.reporting")
    for plugin_type in reporting_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "code_climate" for _, plugin in list(plugins.items())
    )


def test_code_climate_reporting_plugin_report_cc_output():
    """Test the gitlab output of the reporting plugin."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "black", "format", "1", "This is a test", None)
            ]
        }
        _, success = plugin.report(package, issues, "level")
        assert success
        with open(
            os.path.join(
                tmp_dir, "valid_package-level/valid_package-level.code-climate.json"
            )
        ) as cc_file:
            cc_json = json.load(cc_file)[0]
            assert "type" in cc_json
            assert "check_name" in cc_json
            assert "categories" in cc_json
            assert "severity" in cc_json
            assert "description" in cc_json
            assert "location" in cc_json
            assert "fingerprint" in cc_json


def test_code_climate_reporting_plugin_report_gitlab_output():
    """Test the gitlab output of the reporting plugin."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(
            tmp_dir, True, "config-gitlab.yaml"
        )
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", "3", "This is a test", None)
            ]
        }
        _, success = plugin.report(package, issues, "level")
        assert success
        with open(
            os.path.join(
                tmp_dir, "valid_package-level/valid_package-level.code-climate.json"
            )
        ) as cc_file:
            cc_json = json.load(cc_file)[0]
            assert "type" not in cc_json
            assert "check_name" not in cc_json
            assert "categories" not in cc_json
            assert "severity" in cc_json
            assert "description" in cc_json
            assert "location" in cc_json
            assert "fingerprint" in cc_json


def test_code_climate_reporting_plugin_report_cert_reference():
    """Test the output of the reporting plugin where the issue has a CERT reference."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", "5", "This is a test", "CERT")
            ]
        }
        _, success = plugin.report(package, issues, "level")
        assert success


def test_code_climate_reporting_plugin_invalid_severity():
    """Test the output of the reporting plugin where the issue has an invalid severity
    type."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(tmp_dir)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue(
                    "test.txt",
                    1,
                    "tool_a",
                    "type",
                    "invalid_severity",
                    "This is a test",
                    None,
                )
            ]
        }
        _, success = plugin.report(package, issues, "level")
        with open(
            os.path.join(
                tmp_dir, "valid_package-level/valid_package-level.code-climate.json"
            )
        ) as cc_file:
            cc_json = json.load(cc_file)[0]
            assert cc_json["severity"] == "info"
        assert success


def test_code_climate_reporting_plugin_report_no_plugin_context():
    """Test the output of the reporting plugin without plugin context."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(tmp_dir, False)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        issues = {
            "tool_a": [
                Issue("test.txt", 1, "tool_a", "type", "1", "This is a test", None)
            ]
        }
        _, success = plugin.report(package, issues, "level")
        assert not success


def test_code_climate_reporting_plugin_report_no_output_directory():
    """Test the output of the reporting plugin without an output directory."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(
            tmp_dir, use_output_directory=False
        )
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        assert plugin.write_output(package, "level", "line")


def test_code_climate_reporting_plugin_report_output_directory_is_none():
    """Test the output of the reporting plugin without an output directory."""
    plugin = setup_code_climate_reporting_plugin(None)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    assert plugin.write_output(package, "level", "line")


def test_code_climate_reporting_plugin_report_fileexists():
    """Test the output of the reporting plugin if there's a file where the output dir
    should go."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(tmp_dir)
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
        _, success = plugin.report(package, issues, "level")
        assert os.path.isfile(
            os.path.join(
                plugin.plugin_context.args.output_directory, "valid_package-level"
            )
        )
    assert not success


def test_code_climate_reporting_plugin_write_output_no_plugin_context():
    """Test the write output method of the reporting plugin without plugin context."""
    with TemporaryDirectory() as tmp_dir:
        plugin = setup_code_climate_reporting_plugin(tmp_dir, False)
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        assert plugin.write_output(package, "level", "line")
        output_file = os.path.join(
            os.getcwd(), package.name + "-" + "level" + ".code-climate.json"
        )
        if os.path.exists(output_file):
            os.remove(output_file)
