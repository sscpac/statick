"""Unit tests for the PyCodeStyle plugin."""
import argparse
import mock
import os
import subprocess
from importlib.metadata import entry_points

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.pydocstyle import PydocstyleToolPlugin
from statick_tool.resources import Resources


def setup_pydocstyle_tool_plugin():
    """Initialize and return a PyCodeStyle plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    pdstp = PydocstyleToolPlugin()
    pdstp.set_plugin_context(plugin_context)
    return pdstp


def test_pydocstyle_tool_plugin_found():
    """Test that the plugin manager can find the PyDocStyle plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "pydocstyle" for _, plugin in list(plugins.items())
    )


def test_pydocstyle_tool_plugin_scan_valid():
    """Integration test: Make sure the pydocstyle output hasn't changed."""
    pdstp = setup_pydocstyle_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "d103.py")
    ]
    issues = pdstp.scan(package, "level")
    assert len(issues) == 1


def test_pydocstyle_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of pydocstyle."""
    pdstp = setup_pydocstyle_tool_plugin()
    output = "valid_package/d103.py:3 in public function `some_method`:\n\
 D103: Missing docstring in public function"
    issues = pdstp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/d103.py"
    assert issues[0].line_number == "3"
    assert issues[0].tool == "pydocstyle"
    assert issues[0].issue_type == "D103"
    assert issues[0].severity == "5"
    assert issues[0].message == "Missing docstring in public function"


def test_pydocstyle_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of pydocstyle."""
    pdstp = setup_pydocstyle_tool_plugin()
    output = "invalid text"
    issues = pdstp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.pydocstyle.subprocess.check_output")
def test_pydocstyle_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means tool hit an
    error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    pdstp = setup_pydocstyle_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "d103.py")
    ]
    issues = pdstp.scan(package, "level")
    assert issues is None

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    issues = pdstp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.pydocstyle.subprocess.check_output")
def test_pydocstyle_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means tool doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked_error")
    pdstp = setup_pydocstyle_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "d103.py")
    ]
    issues = pdstp.scan(package, "level")
    assert issues is None
