"""Unit tests for the console reporting plugin."""

import os
import sys

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugins.reporting.print_to_console import (
    PrintToConsoleReportingPlugin,
)

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_console_reporting_plugin_found():
    """Test that the plugin manager finds the console reporting plugin."""
    plugins = {}
    reporting_plugins = entry_points(group="statick_tool.plugins.reporting")
    for plugin_type in reporting_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "print_to_console" for _, plugin in list(plugins.items())
    )


def test_console_reporting_plugin_report_cert(capsys):
    """Test the output of the reporting plugin."""
    ptcrp = PrintToConsoleReportingPlugin()
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
    output = captured.out.splitlines()
    assert output == [
        "Tool tool_a: 1 unique issues",
        "  test.txt:1: tool_a:type: This is a test (MEM50-CPP) [1]",
        "1 total unique issues",
    ]


def test_console_reporting_plugin_report_nocert(capsys):
    """Test the output of the reporting plugin without a CERT reference."""
    ptcrp = PrintToConsoleReportingPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = {
        "tool_a": [Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", None)]
    }

    ptcrp.report(package, issues, "level")
    captured = capsys.readouterr()
    output = captured.out.splitlines()
    assert output == [
        "Tool tool_a: 1 unique issues",
        "  test.txt:1: tool_a:type: This is a test [1]",
        "1 total unique issues",
    ]
