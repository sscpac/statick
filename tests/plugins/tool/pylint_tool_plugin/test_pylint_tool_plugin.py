"""Unit tests for the Pylint tool plugin."""
import argparse
import multiprocessing
import mock
import os
import subprocess
from importlib.metadata import entry_points

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.pylint import PylintToolPlugin
from statick_tool.resources import Resources


def setup_pylint_tool_plugin(max_procs=1):
    """Construct and return an instance of the Pylint plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin_context.args.max_procs = max_procs
    pltp = PylintToolPlugin()
    pltp.set_plugin_context(plugin_context)
    return pltp


def test_pylint_tool_plugin_found():
    """Test that the plugin manager finds the Pylint plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "pylint" for _, plugin in list(plugins.items())
    )


def test_pylint_tool_plugin_scan_valid():
    """Integration test: Make sure the pylint output hasn't changed."""
    pltp = setup_pylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "basic.py")
    ]
    issues = pltp.scan(package, "level")
    # We expect to have missing docstring and unused import warnings.
    assert len(issues) == 2


def test_pylint_tool_plugin_scan_valid_max_cpu_cores():
    """Integration test: Make sure the pylint output hasn't changed when using max CPU
    cores."""
    max_procs = multiprocessing.cpu_count()
    pltp = setup_pylint_tool_plugin(max_procs=max_procs)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "basic.py")
    ]
    issues = pltp.scan(package, "level")
    # We expect to have missing docstring and unused import warnings.
    assert len(issues) == 2


def test_pylint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of pylint."""
    pltp = setup_pylint_tool_plugin()
    output = "basic.py:1: [W0611(unused-import), ] Unused import subprocess"
    issues = pltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "basic.py"
    assert issues[0].line_number == "1"
    assert issues[0].tool == "pylint"
    assert issues[0].issue_type == "W0611(unused-import)"
    assert issues[0].severity == "5"
    assert issues[0].message == "Unused import subprocess"

    output = "basic.py:1: [W0611(unused-import)] Unused import subprocess"
    issues = pltp.parse_output([output])
    assert issues[0].message == "Unused import subprocess"

    output = "basic.py:1: [W0611(unused-import), not-empty] Unused import subprocess"
    issues = pltp.parse_output([output])
    assert issues[0].message == "not-empty: Unused import subprocess"


def test_pylint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of pylint."""
    pltp = setup_pylint_tool_plugin()
    output = "invalid text"
    issues = pltp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.pylint.subprocess.check_output")
def test_pylint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means pylint hit
    an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    pltp = setup_pylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pylint_test.py")
    ]
    issues = pltp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = pltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.pylint.subprocess.check_output")
def test_pylint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means pylint doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    pltp = setup_pylint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "pylint_test.py")
    ]
    issues = pltp.scan(package, "level")
    assert issues is None
