"""Unit tests for the TeX discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.tex_discovery_plugin.tex_discovery_plugin import \
    TexDiscoveryPlugin


def test_tex_plugin_found():
    """Test that the plugin manager finds the TeX discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "tex"
    assert any(plugin_info.plugin_object.get_name() == 'tex' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))
    # While we're at it, verify that a plugin is named C Discovery Plugin
    assert any(plugin_info.name == 'TeX Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))


def test_tex_plugin_scan_valid():
    """Test that the TeX discovery plugin finds valid TeX source and bib files."""
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    tdp = TexDiscoveryPlugin()
    tdp.scan(package, 'level')
    expected = ['test.tex', 'test.bib']
    if tdp.file_command_exists():
        expected += ['oddextensiontex.source']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename)
                         for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package['tex']) == set(expected_fullpath)


def test_tex_plugin_scan_invalid():
    """Test that the TeX discovery plugin doesn't find non-TeX files."""
    package = Package('invalid_package',
                      os.path.join(os.path.dirname(__file__),
                                   'invalid_package'))
    tdp = TexDiscoveryPlugin()
    tdp.scan(package, 'level')
    assert not package['tex']
