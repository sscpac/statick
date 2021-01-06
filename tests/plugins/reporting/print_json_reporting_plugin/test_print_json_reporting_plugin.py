"""Unit tests for the console reporting plugin."""
import json
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugins.reporting.print_json_reporting_plugin import (
    PrintJsonReportingPlugin,
)
from statick_tool.reporting_plugin import ReportingPlugin


def test_print_json_reporting_plugin_found():
    """Test that the plugin manager finds the print json reporting plugin."""
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
    assert any(
        plugin_info.plugin_object.get_name() == "print_json"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
    )
    assert any(
        plugin_info.name == "Print JSON Reporting Plugin"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
    )


def test_print_json_reporting_plugin_report_cert(capsys):
    """Test the output of the reporting plugin."""
    ptcrp = PrintJsonReportingPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = {
        "tool_a": [
            Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", "MEM50-CPP")
        ]
    }

    ptcrp.report(package, issues, "level")
    captured = capsys.readouterr()
    output = captured.out.splitlines()[0]
    assert (
        output
        == '{"issues": [{"fileName": "test.txt", "lineNumber": 1, "tool": "tool_a", "type": "type", "severity": 1, "message": "This is a test", "certReference": "MEM50-CPP"}]}'
    )
    assert json.loads(output)


def test_print_json_reporting_plugin_report_nocert(capsys):
    """Test the output of the reporting plugin."""
    ptcrp = PrintJsonReportingPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = {
        "tool_a": [
            Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", None),
            Issue("test2.txt", 2, "tool_b", "type", 2, "This is a second test", None),
        ]
    }

    ptcrp.report(package, issues, "level")
    captured = capsys.readouterr()
    output = captured.out.splitlines()[0]
    assert (
        output
        == '{"issues": [{"fileName": "test.txt", "lineNumber": 1, "tool": "tool_a", "type": "type", "severity": 1, "message": "This is a test", "certReference": ""}, {"fileName": "test2.txt", "lineNumber": 2, "tool": "tool_b", "type": "type", "severity": 2, "message": "This is a second test", "certReference": ""}]}'
    )
    assert json.loads(output)
