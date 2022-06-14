"""Unit tests for the make tool plugin."""
import argparse
import os
import subprocess

import mock
import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.make_tool_plugin import MakeToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_make_tool_plugin():
    """Construct and return an instance of the Make plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    mtp = MakeToolPlugin()
    mtp.set_plugin_context(plugin_context)
    return mtp


def test_make_tool_plugin_found():
    """Test that the plugin manager finds the Make plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {
            "Tool": ToolPlugin,
        }
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "make"
    assert any(
        plugin_info.plugin_object.get_name() == "make"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named Yamllint Tool Plugin
    assert any(
        plugin_info.name == "Make Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_make_tool_plugin_scan_valid():
    """Integration test: Make sure the make output hasn't changed."""
    mtp = setup_make_tool_plugin()
    if not mtp.command_exists("make"):
        pytest.skip("Missing make executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = "make_targets"
    issues = mtp.scan(package, "level")
    assert not issues


def test_make_tool_plugin_scan_missing_tool_name():
    """Check that a missing tool name results in an empty list of issues."""
    mtp = setup_make_tool_plugin()
    if not mtp.command_exists("make"):
        pytest.skip("Missing make executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = mtp.scan(package, "level")
    assert not issues


def test_make_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of make."""
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    output = "valid_package/hello.c:7:3: error: expected ; before return"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/hello.c"
    assert issues[0].line_number == "7"
    assert issues[0].severity == "5"
    assert issues[0].message == "expected ; before return"


def test_make_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of make."""
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    output = "invalid text"
    issues = mtp.parse_package_output(package, output)
    assert not issues


def test_make_tool_plugin_parse_overloaded_virtual():
    """Verify that we can parse the output of make with overloaded-virtual."""
    mtp = setup_make_tool_plugin()
    package = Package("valid_package", "/home/user/valid_package")
    output = (
        "/home/user/valid_package/hello.c:7:3: error: overloaded-virtual: \n"
        "/home/user/valid_package/hello.c:7:3: error: second line"
    )
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/hello.c"
    assert issues[0].line_number == "7"
    assert issues[0].severity == "5"
    assert issues[0].message == "overloaded-virtual: second line"


def test_make_tool_plugin_parse_warning_levels():
    """Verify that we can parse the warning levels of make output."""
    mtp = setup_make_tool_plugin()
    package = Package("valid_package", "/home/user/valid_package")
    output = "/home/user/valid_package/hello.c:7:3: fatal error: This is a fatal error"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/hello.c"
    assert issues[0].line_number == "7"
    assert issues[0].severity == "5"
    assert issues[0].message == "This is a fatal error"
    assert issues[0].issue_type == "fatal-error"

    output = "/home/user/valid_package/hello.c:8:3: warning: This is a warning"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/hello.c"
    assert issues[0].line_number == "8"
    assert issues[0].severity == "3"
    assert issues[0].message == "This is a warning"
    assert issues[0].issue_type == "unknown-error"

    output = "/home/user/valid_package/hello.c:8:3: notype: This is not a type"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/hello.c"
    assert issues[0].line_number == "8"
    assert issues[0].severity == "3"
    assert issues[0].message == "This is not a type"
    assert issues[0].issue_type == "unknown-error"

    # Any note type output is filtered from results. I'm not sure that's what we
    # really want, but changing it would break expected results.
    output = "/home/user/valid_package/hello.c:9:3: note: This is a note"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 0


def test_make_tool_plugin_parse_linker_error():
    """Verify that we can parse a linker error in make output."""
    mtp = setup_make_tool_plugin()
    package = Package("valid_package", "/home/user/valid_package")
    output = "collect2: ld returned 1 exit status"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "Linker"
    assert issues[0].line_number == "0"
    assert issues[0].severity == "5"
    assert issues[0].message == "Linking failed"
    assert issues[0].issue_type == "linker"


def test_make_tool_plugin_parse_warnings_mapping():
    """Verify that we can associate a make warning with a SEI Cert warning."""
    mtp = setup_make_tool_plugin()
    package = Package("valid_package", "/home/user/valid_package")
    output = "/home/user/valid_package/hello.cpp:8:3: warning: 'Class::i_' will be initialized after [-Wreorder]"
    issues = mtp.parse_package_output(package, output)
    assert len(issues) == 1
    assert issues[0].filename == "/home/user/valid_package/hello.cpp"
    assert issues[0].line_number == "8"
    assert issues[0].severity == "3"
    assert issues[0].message == "'Class::i_' will be initialized after [-Wreorder]"
    assert issues[0].issue_type == "-Wreorder"
    assert issues[0].cert_reference == "OOP53-CPP"


@mock.patch("statick_tool.plugins.tool.make_tool_plugin.subprocess.check_output")
def test_make_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means make hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = "make_targets"
    issues = mtp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.make_tool_plugin.subprocess.check_output")
def test_make_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means make doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    mtp = setup_make_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = "make_targets"
    issues = mtp.scan(package, "level")
    assert issues is None
