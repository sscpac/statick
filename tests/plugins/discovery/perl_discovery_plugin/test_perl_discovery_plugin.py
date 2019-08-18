"""Unit tests for the Perl discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.perl_discovery_plugin import \
    PerlDiscoveryPlugin


def test_perl_discovery_plugin_found():
    """Test that the plugin manager finds the Perl discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces([os.path.join(os.path.dirname(statick_tool.__file__),
                                          'plugins')])
    manager.setCategoriesFilter({
        "Discovery": DiscoveryPlugin,
    })
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "perl"
    assert any(plugin_info.plugin_object.get_name() == 'perl' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))
    # While we're at it, verify that a plugin is named Perl Discovery Plugin
    assert any(plugin_info.name == 'Perl Discovery Plugin' for
               plugin_info in manager.getPluginsOfCategory("Discovery"))


def test_perl_discovery_plugin_scan_valid():
    """Test that the Perl discovery plugin finds valid perl files."""
    pldp = PerlDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    pldp.scan(package, 'level', None)
    expected = ['test.pl', 'ignore_this/ignoreme.pl']
    if pldp.file_command_exists():
        expected += ['oddextensionpl.source']
    # We have to add the path to each of the above...yuck
    expected_fullpath = [os.path.join(package.path, filename)
                         for filename in expected]
    # Neat trick to verify that two unordered lists are the same
    assert set(package['perl_src']) == set(expected_fullpath)


def test_perl_discovery_plugin_scan_exceptions():
    """Test that the perl discovery plugin properly respects exceptions."""
    pldp = PerlDiscoveryPlugin()
    package = Package('valid_package', os.path.join(os.path.dirname(__file__),
                                                    'valid_package'))
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), 'exceptions.yaml'))
    pldp.scan(package, 'level', exceptions)
    expected_src = ['test.pl', 'oddextensionpl.source']
    # We have to add the path to each of the above...yuck
    expected_src_fullpath = [os.path.join(package.path, filename)
                             for filename in expected_src]
    # Neat trick to verify that two unordered lists are the same
    assert set(package['perl_src']) == set(expected_src_fullpath)
