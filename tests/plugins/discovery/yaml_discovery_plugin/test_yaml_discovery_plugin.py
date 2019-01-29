import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.yaml_discovery_plugin import \
    YAMLDiscoveryPlugin


def test_yaml_discovery_plugin_found():
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "yaml"
    assert(any(plugin_info.plugin_object.get_name() == 'yaml' for
               plugin_info in manager.getPluginsOfCategory("Discovery")))
    # While we're at it, verify that a plugin is named C Discovery Plugin
    assert(any(plugin_info.name == 'YAML Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery")))


def test_yaml_discovery_plugin_scan_valid():
    ydp = YAMLDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    ydp.scan(package, 'level')
    expected = ['test.yaml']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename)
                         for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert(set(package['yaml']) == set(expected_fullpath))


def test_yaml_discovery_plugin_scan_invalid_nocmake():
    ydp = YAMLDiscoveryPlugin()
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    ydp.scan(package, 'level')
    assert(not package['yaml'])
