"""Unit tests for the CMake discovery plugin."""
import argparse
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.config import Config
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.discovery.cmake_discovery_plugin import \
    CMakeDiscoveryPlugin
from statick_tool.resources import Resources


def setup_cmake_discovery_plugin():
    """Create an instance of the CMake discovery plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--show-tool-output", dest="show_tool_output",
                            action="store_true", help="Show tool output")

    resources = Resources([os.path.join(os.path.dirname(statick_tool.__file__),
                                        'plugins')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    cmdp = CMakeDiscoveryPlugin()
    cmdp.set_plugin_context(plugin_context)
    return cmdp


def test_cmake_discovery_plugin_found():
    """Test that the plugin manager finds the CMake discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "cmake"
    assert any(plugin_info.plugin_object.get_name() == 'cmake' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))
    # While we're at it, verify that a plugin is named CMake Discovery Plugin
    assert any(plugin_info.name == 'CMake Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))


def test_cmake_discovery_plugin_scan_valid():
    """Test the CMake discovery plugin with a valid directory."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    cmdp.scan(package, 'level')
    assert package['cmake']


def test_cmake_discovery_plugin_scan_invalid():
    """Test the CMake discovery plugin with an invalid directory."""
    cmdp = setup_cmake_discovery_plugin()
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    cmdp.scan(package, 'level')
    assert not package['cmake']
