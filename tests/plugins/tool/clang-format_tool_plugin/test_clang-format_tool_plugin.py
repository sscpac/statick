"""Unit tests for the clang-format plugin."""
import argparse
import os
import shutil
import subprocess

import mock
import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.clang_format_tool_plugin import ClangFormatToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_clang_format_tool_plugin(use_plugin_context=True):
    """Initialize and return an instance of the clang-format plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--clang-format-bin", dest="clang_format_bin")
    arg_parser.add_argument(
        "--clang-format-raise-exception",
        dest="clang_format_raise_exception",
        action="store_false",
        default=True,
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    cftp = ClangFormatToolPlugin()
    if use_plugin_context:
        cftp.set_plugin_context(plugin_context)
    return cftp


def setup_clang_format_tool_plugin_non_default():
    """Initialize and return an instance of the clang-format plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )
    arg_parser.add_argument("--clang-format-bin", dest="clang_format_bin")
    arg_parser.add_argument(
        "--clang-format-raise-exception",
        dest="clang_format_raise_exception",
        action="store_true",
        default=False,
    )
    arg_parser.add_argument("--output-directory", dest="output_directory")

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    cftp = ClangFormatToolPlugin()
    cftp.set_plugin_context(plugin_context)
    return cftp


def test_clang_format_tool_plugin_found():
    """Test that the plugin manager can find the clang-format plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {"Tool": ToolPlugin,}
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "clang_format"
    assert any(
        plugin_info.plugin_object.get_name() == "clang-format"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named clang-format Tool Plugin
    assert any(
        plugin_info.name == "clang-format Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_clang_format_tool_plugin_scan_valid():
    """Integration test: Make sure the clang_format output hasn't changed."""
    cftp = setup_clang_format_tool_plugin()
    if not cftp.command_exists("clang-format"):
        pytest.skip("Missing clang-format executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Copy the latest clang_format over
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert len(issues) == 1


def test_clang_format_tool_plugin_scan_no_plugin_context():
    """Test that issues are None when no plugin context is provided."""
    cftp = setup_clang_format_tool_plugin(False)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert not issues


def test_clang_format_tool_plugin_scan_missing_fields():
    """Test that issues are empty when fields are missing from the package."""
    cftp = setup_clang_format_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Issues should be empty until make_targets is added to the package.
    issues = cftp.scan(package, "level")
    assert not issues


def test_clang_format_tool_plugin_scan_missing_config_file():
    """Test that issues are None when configuration file is different."""
    cftp = setup_clang_format_tool_plugin()
    with open(os.path.join(os.path.expanduser("~"), "_clang-format"), "a") as fin:
        fin.write("invalid entry")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert issues is None


def test_clang_format_tool_plugin_scan_missing_config_file_non_default():
    """Test that issues is empty when configuration file is different."""
    cftp = setup_clang_format_tool_plugin_non_default()
    with open(os.path.join(os.path.expanduser("~"), "_clang-format"), "a") as fin:
        fin.write("invalid entry")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert not issues


def test_clang_format_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of clang_format."""
    cftp = setup_clang_format_tool_plugin()
    output = "valid_package/indents.c\n\
<?xml version='1.0'?>\n\
<replacements xml:space='preserve' incomplete_format='false'>\n\
<replacement offset='12' length='1'>&#10;  </replacement>\n\
</replacements>"
    issues = cftp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/indents.c"
    assert issues[0].line_number == "0"
    assert issues[0].tool == "clang-format"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == "1"
    assert issues[0].message == "1 replacements"


def test_clang_format_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of clang_format."""
    cftp = setup_clang_format_tool_plugin()
    output = "invalid text"
    issues = cftp.parse_output(output)
    assert not issues


def test_clang_format_tool_plugin_custom_config_diff():
    """Verify that we can identify a diff between actual and target formats."""
    cftp = setup_clang_format_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    cftp.plugin_context.resources
    # Issues should be empty until make_targets is added to the package.
    issues = cftp.scan(package, "level")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.clang_format_tool_plugin.subprocess.check_output"
)
def test_clang_format_tool_plugin_scan_calledprocesserror_non_default(
    mock_subprocess_check_output,
):
    """
    Test what happens when a CalledProcessError is raised (usually means clang-format hit an error).

    Expected result: issues is empty
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    cftp = setup_clang_format_tool_plugin_non_default()
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["headers"] = []
    issues = cftp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.clang_format_tool_plugin.open")
def test_clang_format_tool_plugin_scan_oserror_no_raise(mock_open):
    """
    Test what happens when OSError is raised (usually means clang-format configuration is missing).

    Expected result: issues is empty
    """
    mock_open.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin_non_default()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["headers"] = []
    issues = cftp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.clang_format_tool_plugin.open")
def test_clang_format_tool_plugin_scan_oserror_raise(mock_open):
    """
    Test what happens when OSError is raised (usually means clang-format configuration is missing).

    Expected result: issues is None
    """
    mock_open.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["headers"] = []
    issues = cftp.scan(package, "level")
    assert issues is None


@mock.patch(
    "statick_tool.plugins.tool.clang_format_tool_plugin.subprocess.check_output"
)
def test_clang_format_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means clang-format doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin()
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert issues is None


@mock.patch(
    "statick_tool.plugins.tool.clang_format_tool_plugin.subprocess.check_output"
)
def test_clang_format_tool_plugin_scan_oserror_raise_bin(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means clang-format doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin_non_default()
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert not issues
