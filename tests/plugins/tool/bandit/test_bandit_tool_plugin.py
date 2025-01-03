"""Unit tests for the bandit tool module."""

import argparse
import os
import subprocess
import sys

import mock

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.bandit import BanditToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_bandit_tool_plugin(binary=None):
    """Create an instance of the bandit plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--bandit-bin", dest="bandit_bin")
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    btp = BanditToolPlugin()
    if binary:
        plugin_context.args.bandit_bin = binary
    btp.set_plugin_context(plugin_context)
    return btp


def test_bandit_tool_plugin_found():
    """Test that the bandit tool plugin is detected by the plugin system."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "bandit" for _, plugin in list(plugins.items())
    )


def test_bandit_tool_plugin_scan_valid():
    """Integration test: Make sure the bandit output hasn't changed."""
    btp = setup_bandit_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "b404.py")
    ]
    issues = btp.scan(package, "level")
    assert len(issues) == 1


def test_bandit_tool_plugin_scan_no_src():
    """Test what happens when we don't have python_src in package.

    Expected result: issues is an empty list
    """
    btp = setup_bandit_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = btp.scan(package, "level")
    assert len(issues) == 0


def test_bandit_tool_plugin_scan_empty_src():
    """Test what happens when python_src is an empty list.

    Expected result: issues is an empty list
    """
    btp = setup_bandit_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = []
    issues = btp.scan(package, "level")
    assert len(issues) == 0


def test_bandit_tool_plugin_scan_wrong_binary():
    """Test what happens when the specified tool binary does not exist.

    Expected result: issues is None
    """
    btp = setup_bandit_tool_plugin("wrong_binary")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "b404.py")
    ]
    issues = btp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.bandit.subprocess.check_output")
def test_bandit_tool_plugin_scan_empty_oserror(mock_subprocess_check_output):
    """Test what happens an OSError is hit (such as if bandit doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    btp = setup_bandit_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "b404.py")
    ]
    issues = btp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.bandit.subprocess.check_output")
def test_bandit_tool_plugin_scan_empty_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is hit (such as if bandit encounters
    an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    btp = setup_bandit_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "b404.py")
    ]
    issues = btp.scan(package, "level")
    assert issues is None


def test_bandit_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of bandit."""
    btp = setup_bandit_tool_plugin()
    output = [
        "filename,test_name,test_id,issue_severity,issue_confidence,issue_text,line_number,line_range,more_info",
        "valid_package/b404.py,blacklist,B404,LOW,HIGH,Consider possible security implications associated with subprocess module.,1,[1],https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess",
    ]
    issues = btp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/b404.py"
    assert issues[0].line_number == "1"
    assert issues[0].tool == "bandit"
    assert issues[0].issue_type == "B404"
    assert issues[0].severity == "5"
    assert (
        issues[0].message
        == "Consider possible security implications associated with subprocess module."
    )

    output = [
        "filename,test_name,test_id,issue_severity,issue_confidence,issue_text,line_number,line_range,more_info",
        "valid_package/b404.py,blacklist,B404,LOW,MEDIUM,Consider possible security implications associated with subprocess module.,1,[1],https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess",
    ]
    issues = btp.parse_output(output)
    assert len(issues) == 1
    assert issues[0].severity == "3"


def test_bandit_tool_plugin_parse_invalid():
    """Verify that we don't return anything on bad input."""
    btp = setup_bandit_tool_plugin()
    output = "invalid text"
    issues = btp.parse_output(output)
    assert not issues
