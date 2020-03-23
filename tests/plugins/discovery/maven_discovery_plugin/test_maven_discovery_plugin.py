"""Unit tests for the Maven discovery plugin."""
import os

from yapsy.PluginManager import PluginManager

import statick_tool
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package
from statick_tool.plugins.discovery.maven_discovery_plugin import MavenDiscoveryPlugin


def test_maven_discovery_plugin_found():
    """Test that the plugin manager finds the Maven discovery plugin."""
    manager = PluginManager()
    # Get the path to statick_tool/__init__.py, get the directory part, and
    # add 'plugins' to that to get the standard plugins dir
    manager.setPluginPlaces(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    manager.setCategoriesFilter(
        {"Discovery": DiscoveryPlugin,}
    )
    manager.collectPlugins()
    # Verify that a plugin's get_name() function returns "java"
    assert any(
        plugin_info.plugin_object.get_name() == "maven"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )
    # While we're at it, verify that a plugin is named Maven Discovery Plugin
    assert any(
        plugin_info.name == "Maven Discovery Plugin"
        for plugin_info in manager.getPluginsOfCategory("Discovery")
    )


def test_maven_discovery_plugin_scan_single():
    """Test that the Maven discovery plugin finds a single pom.xml."""
    mdp = MavenDiscoveryPlugin()
    package = Package(
        "single_package", os.path.join(os.path.dirname(__file__), "single_package")
    )
    mdp.scan(package, "level")
    expected_top = ["pom.xml"]
    # We have to add the path to each of the above...yuck
    expected_top_fullpath = [
        os.path.join(package.path, filename) for filename in expected_top
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["top_poms"]) == set(expected_top_fullpath)
    assert set(package["all_poms"]) == set(expected_top_fullpath)


def test_maven_discovery_plugin_scan_same_depth():
    """Test that the Maven discovery plugin finds two pom.xml files at the same depth."""
    mdp = MavenDiscoveryPlugin()
    package = Package(
        "two_package", os.path.join(os.path.dirname(__file__), "two_package")
    )
    mdp.scan(package, "level")
    expected_top = [os.path.join("a", "pom.xml"), os.path.join("b", "pom.xml")]
    expected_top_fullpath = [
        os.path.join(package.path, filename) for filename in expected_top
    ]
    assert set(package["top_poms"]) == set(expected_top_fullpath)
    assert set(package["all_poms"]) == set(expected_top_fullpath)


def test_maven_discovery_plugin_scan_multilevel():
    """Test that the Maven discovery plugin finds pom.xml files at multiple depths."""
    mdp = MavenDiscoveryPlugin()
    package = Package(
        "multi_package", os.path.join(os.path.dirname(__file__), "multi_package")
    )
    mdp.scan(package, "level")
    expected_top = [os.path.join("a", "pom.xml"), os.path.join("b", "pom.xml")]
    expected_all = expected_top + [os.path.join("a", "c", "pom.xml")]
    expected_top_fullpath = [
        os.path.join(package.path, filename) for filename in expected_top
    ]
    expected_all_fullpath = [
        os.path.join(package.path, filename) for filename in expected_all
    ]
    assert set(package["top_poms"]) == set(expected_top_fullpath)
    assert set(package["all_poms"]) == set(expected_all_fullpath)
