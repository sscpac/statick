"""Unit tests for the Python discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.python_discovery_plugin import \
    PythonDiscoveryPlugin


def test_python_discovery_plugin_found():
    """Test that the plugin manager finds the Python discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "python"
    assert any(plugin_info.plugin_object.get_name() == 'python' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))
    # While we're at it, verify that a plugin is named Python Discovery Plugin
    assert any(plugin_info.name == 'Python Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))


def test_python_discovery_plugin_scan_valid():
    """Test that the Python discovery plugin finds valid python files."""
    pydp = PythonDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    pydp.scan(package, 'level')
    expected = ['test.py', 'oddextensionpy.source']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename)
                         for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package['python_src']) == set(expected_fullpath)


def test_python_discovery_plugin_scan_invalid():
    """Test that the discovery plugin doesn't find non-python files."""
    pydp = PythonDiscoveryPlugin()
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    pydp.scan(package, 'level')
    assert not package['python_src']
