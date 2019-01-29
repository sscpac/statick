import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.java_discovery_plugin import \
    JavaDiscoveryPlugin


def test_java_discovery_plugin_found():
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "java"
    assert(any(plugin_info.plugin_object.get_name() == 'java' for
               plugin_info in manager.getPluginsOfCategory("Discovery")))
    # While we're at it, verify that a plugin is named Java Discovery Plugin
    assert(any(plugin_info.name == 'Java Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery")))


def test_java_discovery_plugin_scan_valid():
    jdp = JavaDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    jdp.scan(package, 'level')
    expected_src = ['test.java']
    expected_bin = ['test.class']
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [os.path.join(package.path, filename)
                             for filename in expected_src]
    expected_bin_fullpath = [os.path.join(package.path, filename)
                             for filename in expected_bin]
    # Neat trick to verify that two unordered lists are the same
    assert(set(package['java_src']) == set(expected_src_fullpath))
    assert(set(package['java_bin']) == set(expected_bin_fullpath))


def test_java_discovery_plugin_scan_invalid_nocmake():
    jdp = JavaDiscoveryPlugin()
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    jdp.scan(package, 'level')
    assert(not package['java_src'])
    assert(not package['java_bin'])
