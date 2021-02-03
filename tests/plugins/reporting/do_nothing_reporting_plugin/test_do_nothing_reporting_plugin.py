"""Unit tests for the do nothing reporting plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugins.reporting.do_nothing_reporting_plugin import (
    DoNothingReportingPlugin,
)
from statick_tool.reporting_plugin import ReportingPlugin


def test_do_nothing_reporting_plugin_found():
    """Test that the plugin manager finds the do nothing reporting plugin."""
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
        plugin_info.plugin_object.get_name() == "do_nothing"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
    )
    # While we're at it, verify that a plugin is named C Discovery Plugin
    assert any(
        plugin_info.name == "Do Nothing Reporting Plugin"
        for plugin_info in manager.getPluginsOfCategory("Reporting")
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
