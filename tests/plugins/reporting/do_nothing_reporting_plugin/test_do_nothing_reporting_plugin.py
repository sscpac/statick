"""Unit tests for the do nothing reporting plugin."""
import os
from importlib.metadata import entry_points

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugins.reporting.do_nothing import DoNothingReportingPlugin


def test_do_nothing_reporting_plugin_found():
    """Test that the plugin manager finds the do nothing reporting plugin."""
    plugins = {}
    reporting_plugins = entry_points(group="statick_tool.plugins.reporting")
    for plugin_type in reporting_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "do_nothing" for _, plugin in list(plugins.items())
    )


def test_do_nothing_reporting_plugin_report_cert(capsys):
    """Test the output of the do nothing plugin."""
    dnrp = DoNothingReportingPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = {
        "tool_a": [
            Issue("test.txt", 1, "tool_a", "type", 1, "This is a test", "MEM50-CPP")
        ]
    }

    dnrp.report(package, issues, "level")
    captured = capsys.readouterr()
    output = captured.out.splitlines()
    assert not output
