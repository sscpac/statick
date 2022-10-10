"""Unit tests for the hadolint plugin."""

import argparse
import json
import os
import subprocess
import sys

import mock
import pytest
from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.hadolint_tool_plugin import HadolintToolPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def setup_hadolint_tool_plugin(
    binary=None, use_docker=False, package_dir="valid_package"
):
    """Initialize and return an instance of the hadolint plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--hadolint-bin", dest="hadolint_bin")
    if use_docker:
        arg_parser.add_argument(
            "--hadolint-docker",
            dest="hadolint_docker",
            action="store_false",
        )
    else:
        arg_parser.add_argument(
            "--hadolint-docker",
            dest="hadolint_docker",
            action="store_true",
        )

    resources = Resources(
        [
            os.path.join(os.path.dirname(statick_tool.__file__), "plugins"),
            os.path.join(os.path.dirname(__file__), package_dir),
        ]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin = HadolintToolPlugin()
    if binary:
        plugin_context.args.hadolint_bin = binary
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_hadolint_tool_plugin_found():
    """Test that the plugin manager can find the hadolint plugin."""
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
    # Verify that a plugin's get_name() function returns "hadolint"
    assert any(
        plugin_info.plugin_object.get_name() == "hadolint"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )
    # While we're at it, verify that a plugin is named hadolint Tool Plugin
    assert any(
        plugin_info.name == "Hadolint Tool Plugin"
        for plugin_info in manager.getPluginsOfCategory("Tool")
    )


def test_hadolint_tool_plugin_gather_args():
    """Test that the hadolint tool plugin arguments are collected."""
    arg_parser = argparse.ArgumentParser()
    plugin = setup_hadolint_tool_plugin()
    plugin.gather_args(arg_parser)
    args = arg_parser.parse_args([])
    assert args.hadolint_bin is None
    assert not args.hadolint_docker

    args = arg_parser.parse_args(["--hadolint-docker"])
    assert args.hadolint_bin is None
    assert args.hadolint_docker

    args = arg_parser.parse_args(["--hadolint-bin", "test-bin"])
    assert args.hadolint_bin == "test-bin"
    assert not args.hadolint_docker


def test_hadolint_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of hadolint."""
    plugin = setup_hadolint_tool_plugin()
    output = '[{"file":"Dockerfile","column":1,"message":"Use COPY instead of ADD for files and folders","code":"DL3020","level":"error","line":3}]'
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "Dockerfile"
    assert issues[0].line_number == "3"
    assert issues[0].tool == "hadolint"
    assert issues[0].issue_type == "DL3020"
    assert issues[0].severity == "5"
    assert issues[0].message == "Use COPY instead of ADD for files and folders"


def test_hadolint_tool_plugin_parse_invalid():
    """Verify that invalid output of hadolint is ignored."""
    plugin = setup_hadolint_tool_plugin()
    output = "invalid text"
    issues = plugin.parse_output(output)
    assert not issues


def test_hadolint_tool_plugin_scan_valid():
    """Integration test: Make sure the hadolint output hasn't changed."""
    plugin = setup_hadolint_tool_plugin()
    if not plugin.command_exists("hadolint"):
        pytest.skip("Missing hadolint executable, skipping test.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile.noissues")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_hadolint_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the hadolint output hasn't changed."""
    plugin = setup_hadolint_tool_plugin()
    if not plugin.command_exists("hadolint"):
        pytest.skip("Missing hadolint executable, skipping test.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    # We expect 4 issues:
    # DL3048 style: Invalid label key.
    # DL3059 info: Multiple consecutive `RUN` instructions. Consider consolidation.
    # DL3007 warning: Using latest is prone to errors...
    # DL3020 error: Use COPY instead of ADD for files and folders
    assert len(issues) == 4


def test_hadolint_tool_plugin_scan_valid_with_issues_with_docker():
    """Integration test: Make sure the hadolint output hasn't changed."""
    plugin = setup_hadolint_tool_plugin(use_docker=True)
    if not plugin.command_exists("docker"):
        pytest.skip("Missing docker executable, skipping test.")
    if sys.platform == "win32":
        pytest.skip(
            "Docker only supports windows containers on windows, skipping test."
        )
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    # We expect 4 issues:
    # DL3048 style: Invalid label key.
    # DL3059 info: Multiple consecutive `RUN` instructions. Consider consolidation.
    # DL3007 warning: Using latest is prone to errors...
    # DL3020 error: Use COPY instead of ADD for files and folders
    assert len(issues) == 4


def test_hadolint_tool_plugin_scan_docker_no_config():
    """Integration test: Make sure the plugin handles not having a config file."""
    plugin = setup_hadolint_tool_plugin(use_docker=True, package_dir="missing_config")
    if not plugin.command_exists("docker"):
        pytest.skip("Missing docker executable, skipping test.")
    if sys.platform == "win32":
        pytest.skip(
            "Docker only supports windows containers on windows, skipping test."
        )
    package = Package(
        "missing_config", os.path.join(os.path.dirname(__file__), "missing_config")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "missing_config", "Dockerfile"),
        os.path.join(
            os.path.dirname(__file__), "missing_config", "Dockerfile.noissues"
        ),
    ]
    issues = plugin.scan(package, "level")
    # We expect 4 issues:
    # DL3048 style: Invalid label key.
    # DL3059 info: Multiple consecutive `RUN` instructions. Consider consolidation.
    # DL3007 warning: Using latest is prone to errors...
    # DL3020 error: Use COPY instead of ADD for files and folders
    assert len(issues) == 4


def test_hadolint_tool_plugin_scan_docker_duplicate_format():
    """Integration test: Make sure the plugin handles json errors."""
    plugin = setup_hadolint_tool_plugin(use_docker=True, package_dir="duplicate_format")
    if not plugin.command_exists("docker"):
        pytest.skip("Missing docker executable, skipping test.")
    if sys.platform == "win32":
        pytest.skip(
            "Docker only supports windows containers on windows, skipping test."
        )
    package = Package(
        "duplicate_format", os.path.join(os.path.dirname(__file__), "duplicate_format")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "duplicate_format", "Dockerfile"),
        os.path.join(
            os.path.dirname(__file__), "duplicate_format", "Dockerfile.noissues"
        ),
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 4


@mock.patch("statick_tool.plugins.tool.hadolint_tool_plugin.json.loads")
def test_hadolint_tool_plugin_scan_jsondecodeerror(
    mock_json_loads_jsondecodeerror,
):
    """
    Test what happens when a JSONDecodeError is raised.

    Expected result: issues is None
    """
    mock_json_loads_jsondecodeerror.side_effect = json.decoder.JSONDecodeError(
        pos=0, doc="", msg="mocked error"
    )
    plugin = setup_hadolint_tool_plugin(use_docker=True)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None


def test_hadolint_tool_plugin_scan_different_binary():
    """Test that issues are None when binary is different."""
    plugin = setup_hadolint_tool_plugin(binary="wrong-binary")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.hadolint_tool_plugin.subprocess.check_output")
def test_hadolint_tool_plugin_scan_calledprocesserror(
    mock_subprocess_check_output,
):
    """
    Test what happens when a CalledProcessError is raised (usually means hadolint hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_hadolint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.hadolint_tool_plugin.subprocess.check_output")
def test_hadolint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means hadolint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_hadolint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.hadolint_tool_plugin.subprocess.check_output")
def test_hadolint_tool_plugin_scan_calledprocesserror_with_docker(
    mock_subprocess_check_output,
):
    """
    Test what happens when a CalledProcessError is raised by scan_docker.
    This usually means hadolint hit an error.

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_hadolint_tool_plugin(use_docker=True)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.hadolint_tool_plugin.subprocess.check_output")
def test_hadolint_tool_plugin_scan_oserror_with_docker(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised by scan_docker.
    This usually means hadolint doesn't exist.

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_hadolint_tool_plugin(use_docker=True)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["dockerfile_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "Dockerfile")
    ]
    issues = plugin.scan(package, "level")
    assert issues is None
