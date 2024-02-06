"""Unit tests for the uncrustify plugin."""

import argparse
import mock
import os
import pytest
import subprocess
import sys

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.uncrustify import UncrustifyToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

from tempfile import TemporaryDirectory


def setup_uncrustify_tool_plugin(extra_path=None, use_plugin_context=True, binary=None):
    """Initialize and return an instance of the uncrustify plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--uncrustify-bin", dest="uncrustify_bin")

    paths = []
    if extra_path:
        paths.append(extra_path)
    paths.append(os.path.join(os.path.dirname(statick_tool.__file__), "plugins"))
    resources = Resources(paths)
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    utp = UncrustifyToolPlugin()
    if binary:
        plugin_context.args.uncrustify_bin = binary
    if use_plugin_context:
        utp.set_plugin_context(plugin_context)
    return utp


def test_uncrustify_tool_plugin_found():
    """Test that the plugin manager can find the uncrustify plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "uncrustify" for _, plugin in list(plugins.items())
    )


def test_uncrustify_tool_plugin_scan_valid():
    """Integration test: Make sure the uncrustify output hasn't changed."""
    rsc_path = os.path.join(os.path.dirname(__file__), "valid_package")
    utp = setup_uncrustify_tool_plugin(rsc_path)
    if not utp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test uncrustify plugin")
    elif not utp.command_exists("uncrustify"):
        pytest.skip("Can't find uncrustify, unable to test uncrustify plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    # Need to actually run CMake to generate compile_commands.json
    with TemporaryDirectory() as bin_dir:
        try:
            subprocess.check_output(
                [
                    "cmake",
                    os.path.join(os.path.dirname(__file__), "valid_package"),
                    "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                    "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                    "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=" + bin_dir,
                ],
                universal_newlines=True,
                cwd=bin_dir,
            )
        except subprocess.CalledProcessError as ex:
            print(f"Problem running CMake! Returncode = {str(ex.returncode)}")
            print(f"{ex.output}")
            pytest.fail("Failed running CMake")

        package["make_targets"] = []
        package["make_targets"].append({})
        package["make_targets"][0]["src"] = [
            os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
        ]
        package["headers"] = []
        package["uncrustify"] = "uncrustify"
        issues = utp.scan(package, "level")
    assert len(issues) == 1
    assert issues[0].message == "Uncrustify mis-match"


def test_uncrustify_tool_plugin_scan_no_plugin_context():
    """Test that issues are None when no plugin context is provided."""
    rsc_path = os.path.join(os.path.dirname(__file__), "valid_package")
    utp = setup_uncrustify_tool_plugin(extra_path=rsc_path, use_plugin_context=False)
    if not utp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test uncrustify plugin")
    elif not utp.command_exists("uncrustify"):
        pytest.skip("Can't find uncrustify, unable to test uncrustify plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    issues = utp.scan(package, "level")
    assert issues is None


def test_uncrustify_tool_plugin_scan_wrong_binary():
    """Test that issues are None when wrong binary is provided."""
    rsc_path = os.path.join(os.path.dirname(__file__), "valid_package")
    utp = setup_uncrustify_tool_plugin(extra_path=rsc_path, binary="wrong_binary")
    if not utp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test uncrustify plugin")
    elif not utp.command_exists("uncrustify"):
        pytest.skip("Can't find uncrustify, unable to test uncrustify plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    issues = utp.scan(package, "level")
    assert issues is None


def test_uncrustify_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of uncrustify."""
    utp = setup_uncrustify_tool_plugin()
    output = ""
    issues = utp.parse_output(output)
    assert not issues


def test_uncrustify_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of uncrustify."""
    utp = setup_uncrustify_tool_plugin()
    output = "invalid text"
    issues = utp.parse_output(output)
    assert len(issues) == 12
    assert issues[0].issue_type == "format"
    assert issues[0].message == "Uncrustify mis-match"


def test_uncrustify_tool_plugin_scan_missing_fields():
    """Test what happens when key fields are missing from the Package argument.

    Expected result: issues is None then empty
    """
    utp = setup_uncrustify_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Missing make_targets and headers in package
    issues = utp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.uncrustify.subprocess.check_output")
def test_uncrustify_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means uncrustify doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    utp = setup_uncrustify_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    package["uncrustify"] = "uncrustify"
    issues = utp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.uncrustify.subprocess.check_output")
def test_uncrustify_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means uncrustify
    hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    utp = setup_uncrustify_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    package["uncrustify"] = "uncrustify"
    issues = utp.scan(package, "level")
    assert issues is None
