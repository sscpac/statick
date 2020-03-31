"""Unit tests for the CSS discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.css_discovery_plugin import \
    CSSDiscoveryPlugin


def test_css_plugin_found():
    """Test that the plugin manager finds the css discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "css"
    assert any(plugin_info.plugin_object.get_name() == 'css' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))
    # While we're at it, verify that a plugin is named CSS Discovery Plugin
    assert any(plugin_info.name == 'CSS Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))


def test_css_plugin_scan_valid():
    """Test that the css discovery plugin finds valid css source and bib files."""
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    discovery_plugin = CSSDiscoveryPlugin()
    discovery_plugin.scan(package, 'level')
    expected = ['test.css', os.path.join('ignore_this', 'ignoreme.css')]
    # if discovery_plugin.file_command_exists():
    #     expected += ['oddextensioncss.source']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename)
                         for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package['css_src']) == set(expected_fullpath)


def test_css_plugin_scan_invalid():
    """Test that the css discovery plugin doesn't find non-css files."""
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    discovery_plugin = CSSDiscoveryPlugin()
    discovery_plugin.scan(package, 'level')
    assert not package['css_src']


def test_css_discovery_plugin_scan_exceptions():
    """Test that the css discovery plugin properly respects exceptions."""
    discovery_plugin = CSSDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__),
                                         'exceptions.yaml'))
    discovery_plugin.scan(package, 'level', exceptions)
    expected_src = ['test.css']
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [os.path.join(package.path, filename)
                             for filename in expected_src]
    # Neat trick to verify that two unordered lists are the same
    print("package: {}".format(package['css_src']))
    assert set(package['css_src']) == set(expected_src_fullpath)
