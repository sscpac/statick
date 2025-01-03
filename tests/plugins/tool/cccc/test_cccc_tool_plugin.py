"""Unit tests for the CCCC tool module."""
from __future__ import print_function

import argparse
import os
import shutil
import subprocess
import sys

import mock
import pytest
import xmltodict

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.cccc import CCCCToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_cccc_tool_plugin(use_plugin_context=True, binary=None, cccc_config=None):
    """Create an instance of the CCCC plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--cccc-bin", dest="cccc_bin")
    arg_parser.add_argument("--cccc-config", dest="cccc_config")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    ctp = CCCCToolPlugin()
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    if binary:
        plugin_context.args.cccc_bin = binary
    if cccc_config:
        plugin_context.args.cccc_config = cccc_config
    if use_plugin_context:
        ctp.set_plugin_context(plugin_context)
    return ctp


def test_cccc_tool_plugin_found():
    """Test that the CCCC tool plugin is detected by the plugin system."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "cccc" for _, plugin in list(plugins.items())
    )


# Has issues with not finding the cccc.opts config correctly.
# Plugin probably could use some touching up in this department
def test_cccc_tool_plugin_scan_valid():
    """Integration test: Make sure the CCCC output hasn't changed."""
    ctp = setup_cccc_tool_plugin()

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    print(f"issues: {issues}")
    assert not issues


def test_cccc_tool_plugin_scan_missing_field():
    """Check that a missing set of source files results in empty issues."""
    ctp = setup_cccc_tool_plugin()

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Missing package["c_src"]
    issues = ctp.scan(package, "level")
    assert not issues


def test_cccc_tool_plugin_scan_no_plugin_context():
    """Check that missing plugin context results in empty issues."""
    ctp = setup_cccc_tool_plugin(use_plugin_context=False)

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    assert issues is None


def test_cccc_tool_plugin_scan_missing_config():
    """Check that missing missing configuration file results in empty issues."""
    ctp = setup_cccc_tool_plugin(cccc_config="does_not_exist.opt")

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    assert not issues


def test_cccc_tool_plugin_scan_wrong_bin():
    """Check that an invalid binary results in None."""
    ctp = setup_cccc_tool_plugin(binary="wrong_binary")

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    assert issues is None


def test_cccc_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of CCCC."""
    ctp = setup_cccc_tool_plugin()

    # Copy the latest configuration file over.
    shutil.copyfile(
        ctp.plugin_context.resources.get_file("cccc.opt"),
        os.path.join(os.path.dirname(__file__), "cccc.opt"),
    )
    config_file = ctp.plugin_context.resources.get_file("cccc.opt")

    output_file = os.path.join(os.path.dirname(__file__), "valid_package", "cccc.xml")
    with open(output_file) as f:
        output = xmltodict.parse(f.read())

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = ["tmp/not_a_file.c"]

    issues = ctp.parse_tool_output(output, "tmp/not_a_file.c", config_file)
    assert len(issues) == 2
    assert issues[0].filename == "tmp/not_a_file.c"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "cccc"

    if issues[0].severity == "5":
        assert issues[0].issue_type == "error"
        assert issues[0].severity == "5"
        assert (
            issues[0].message
            == "Example1 - Henry-Kafura/Shepperd measure (overall) - value: 10000.0, thresholds warning: 100.0, error: 1000.0"
        )

        assert issues[1].issue_type == "warn"
        assert issues[1].severity == "3"
        assert (
            issues[1].message
            == "Example1 - Fan in (concrete uses only) - value: 7.0, thresholds warning: 6.0, error: 12.0"
        )
    else:
        assert issues[0].issue_type == "warn"
        assert issues[0].severity == "3"
        assert (
            issues[0].message
            == "Example1 - Fan in (concrete uses only) - value: 7.0, thresholds warning: 6.0, error: 12.0"
        )

        assert issues[1].issue_type == "error"
        assert issues[1].severity == "5"
        assert (
            issues[1].message
            == "Example1 - Henry-Kafura/Shepperd measure (overall) - value: 10000.0, thresholds warning: 100.0, error: 1000.0"
        )


def test_cccc_tool_plugin_parse_missing_names():
    """Verify that we can parse the output of CCCC when fields are missing."""
    ctp = setup_cccc_tool_plugin()

    # Copy the latest configuration file over.
    shutil.copyfile(
        ctp.plugin_context.resources.get_file("cccc.opt"),
        os.path.join(os.path.dirname(__file__), "cccc.opt"),
    )
    config_file = ctp.plugin_context.resources.get_file("cccc.opt")

    output_file = os.path.join(
        os.path.dirname(__file__), "valid_package", "cccc-missing-names.xml"
    )
    with open(output_file) as f:
        output = xmltodict.parse(f.read())

    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = ["tmp/not_a_file.c"]

    issues = ctp.parse_tool_output(output, package, config_file)
    print(f"issues: {issues}")
    assert not issues


def test_cccc_tool_plugin_parse_invalid():
    """Verify that we don't return anything on bad input."""
    ctp = setup_cccc_tool_plugin()
    shutil.copyfile(
        ctp.plugin_context.resources.get_file("cccc.opt"),
        os.path.join(os.path.dirname(__file__), "cccc.opt"),
    )
    config_file = ctp.plugin_context.resources.get_file("cccc.opt")

    output = "invalid text"
    package = {"c_src": "/tmp/not_a_file.c"}
    issues = ctp.parse_tool_output(output, package, config_file)
    assert not issues


def test_cccc_tool_plugin_parse_config_none():
    """Verify that we get empty config if config file is None."""
    ctp = setup_cccc_tool_plugin()
    config = ctp.parse_config(None)
    assert not config


@mock.patch("statick_tool.plugins.tool.cccc.subprocess.check_output")
def test_cccc_tool_plugin_scan_empty_oserror(mock_subprocess_check_output):
    """Test what happens an OSError is hit (such as if cccc doesn't exist)

    Expected result: issues is an empty list
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    ctp = setup_cccc_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.cccc.subprocess.check_output")
def test_cccc_tool_plugin_scan_empty_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is hit (such as if cccc encounters an
    error).

    Expected result: issues is an empty list
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output=b"mocked error"
    )
    ctp = setup_cccc_tool_plugin()
    if not ctp.command_exists("cccc"):
        pytest.skip("Missing cccc executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output=b"mocked error"
    )
    issues = ctp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.cccc.xmltodict.parse")
def test_cccc_tool_plugin_scan_filenotfound(mock_xmltodict_parse):
    """Test what happens when a FileNotFoundError is hit (such as if cccc has no output
    for a file).

    Expected result: issues is an empty list
    """
    mock_xmltodict_parse.side_effect = FileNotFoundError()
    ctp = setup_cccc_tool_plugin()
    if not ctp.command_exists("cccc"):
        pytest.skip("Missing cccc executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["c_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "example.cpp")
    ]
    issues = ctp.scan(package, "level")
    assert not issues
