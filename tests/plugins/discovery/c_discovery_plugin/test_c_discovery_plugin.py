"""Unit tests for the C discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.c_discovery_plugin import CDiscoveryPlugin


def test_c_discovery_plugin_found():
    """Test that the plugin manager finds the C discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "c"
    assert any(plugin_info.plugin_object.get_name() == 'C' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))
    # While we're at it, verify that a plugin is named C Discovery Plugin
    assert any(plugin_info.name == 'C/C++ Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))


def test_c_discovery_plugin_scan_valid():
    """Test that the C discovery plugin finds valid C source/header files."""
    cdp = CDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    cdp.scan(package, 'level')
    expected = ['test.c', 'test.cpp', 'test.cc', 'test.cxx', 'test.h',
                'test.hxx', 'test.hpp', 'oddextensioncpp.source',
                'oddextensionc.source']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename)
                         for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package['c_src']) == set(expected_fullpath)


def test_c_discovery_plugin_scan_invalid_nocmake():
    """Test that the C discovery plugin doesn't find non-C files."""
    cdp = CDiscoveryPlugin()
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    cdp.scan(package, 'level')
    assert not package['c_src']
