"""Unit tests for the CMake discovery plugin."""
import argparse
import os
import subprocess
import sys

import mock

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.discovery.cmake import CMakeDiscoveryPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_cmake_discovery_plugin(add_plugin_context=True, cmake_flags=""):
    """Create an instance of the CMake discovery plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    cmdp = CMakeDiscoveryPlugin()
    if add_plugin_context:
        plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
        plugin_context.args.output_directory = os.path.dirname(__file__)
        plugin_context.args.cmake_flags = cmake_flags
        cmdp.set_plugin_context(plugin_context)
    return cmdp


def test_cmake_discovery_plugin_found():
    """Test that the plugin manager finds the CMake discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "cmake" for _, plugin in list(discovery_plugins.items())
    )


def test_cmake_discovery_plugin_scan_valid():
    """Test the CMake discovery plugin with a valid directory."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["cmake_flags"] = "-DCMAKE_PREFIX_PATH=/opt/ros/foxy"
    cmdp.scan(package, "level")
    assert package["cmake_src"]


def test_cmake_discovery_plugin_scan_invalid():
    """Test the CMake discovery plugin with an invalid directory."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    cmdp.scan(package, "level")
    assert not package["cmake_src"]


def test_cmake_discovery_plugin_scan_no_plugin_context():
    """Test the CMake discovery plugin with an invalid directory."""
    cmdp = setup_cmake_discovery_plugin(False)
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    cmdp.scan(package, "level")
    assert "cmake_src" not in package


def test_cmake_discovery_plugin_empty_cmake_flags():
    """Test the CMake discovery plugin without custom CMake flags."""
    cmdp = setup_cmake_discovery_plugin(True, None)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    cmdp.scan(package, "level")
    assert "cmake_src" in package


def test_cmake_discovery_plugin_cmake_file_extension():
    """Test the CMake discovery plugin finds files with extension cmake."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "cmake_ext_package",
        os.path.join(os.path.dirname(__file__), "cmake_ext_package"),
    )
    cmdp.scan(package, "level")
    assert package["cmake_src"] == [
        os.path.join(
            os.path.dirname(__file__),
            "cmake_ext_package",
            "CMakeModules",
            "FindCython.cmake",
        )
    ]


def test_cmake_discovery_plugin_check_output_headers():
    """Test the CMake discovery plugin finds header files."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["headers"] = []
    header = "/usr/include/foo/bar.h"
    output = "-- HEADERS: {}".format(header)
    cmdp.process_output(output, package)
    assert package["headers"] == [header]


def test_cmake_discovery_plugin_check_output_target():
    """Test the CMake discovery plugin finds target output."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    output = "-- TARGET: [NAME:foo][SRC_DIR:foo/src/][INCLUDE_DIRS:include/foo/][SRC:foo.cpp]"
    output += (
        "\n-- TARGET: [NAME:foo_lib][SRC_DIR:foo/src/][INCLUDE_DIRS:][SRC:foo.cpp]"
    )
    cmdp.process_output(output, package)
    assert package["make_targets"][0]["name"] == "foo"
    assert package["make_targets"][0]["src_dir"] == "foo/src/"
    assert package["make_targets"][0]["include_dirs"] == ["include/foo/"]
    assert package["make_targets"][0]["src"] == ["foo/src/foo.cpp"]
    assert package["make_targets"][1]["name"] == "foo_lib"
    assert package["make_targets"][1]["src_dir"] == "foo/src/"
    assert package["make_targets"][1]["include_dirs"] == [""]
    assert package["make_targets"][1]["src"] == ["foo/src/foo.cpp"]


def test_cmake_discovery_plugin_check_output_project():
    """Test the CMake discovery plugin finds project output."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["bin_dir"] = []
    package["src_dir"] = []
    output = "-- PROJECT: [NAME:foo][SRC_DIR:foo/src/][BIN_DIR:devel/foo/]"
    cmdp.process_output(output, package)
    assert package["bin_dir"] == "devel/foo/"
    assert package["src_dir"] == "foo/src/"


@mock.patch("os.path.isfile")
def test_cmake_discovery_plugin_check_output_roslint(mock_isfile):
    """Test the CMake discovery plugin finds roslint executable."""
    mock_isfile.return_value = True
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["cpplint"] = []
    roslint = "/opt/ros/melodic/lib/roslint/cpplint"
    output = "-- ROSLINT: {}".format(roslint)
    cmdp.process_output(output, package)
    assert package["cpplint"]


@mock.patch("os.path.isfile")
def test_cmake_discovery_plugin_check_output_cpplint_without_roslint_installed(
    mock_isfile,
):
    """Test the CMake discovery plugin finds cpplint executable when roslint is not
    installed."""
    mock_isfile.return_value = False
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["cpplint"] = []
    output = "roslint is not installed"
    cmdp.process_output(output, package)
    assert package["cpplint"]


@mock.patch("os.path.isfile")
def test_cmake_discovery_plugin_check_output_cpplint_with_roslint_installed(
    mock_isfile,
):
    """Test the CMake discovery plugin finds cpplint executable when roslint is
    installed."""
    mock_isfile.return_value = False
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["cpplint"] = []
    roslint = "/opt/ros/noetic/lib/roslint/cpplint"
    output = "-- ROSLINT: {}".format(roslint)
    cmdp.process_output(output, package)
    assert package["cpplint"]


@mock.patch(
    "statick_tool.plugins.discovery.cmake.subprocess.check_output"
)
def test_cmake_discovery_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means CMake hit an
    error).

    Expected result: no make targets exist
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    cmdp = setup_cmake_discovery_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    cmdp.scan(package, "level")
    assert not package["make_targets"]


@mock.patch(
    "statick_tool.plugins.discovery.cmake.subprocess.check_output"
)
def test_cmake_discovery_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means CMake is not
    available).

    Expected result: no make targets exist
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    cmdp = setup_cmake_discovery_plugin()
    cmdp.scan(package, "level")
    assert not package["make_targets"]
