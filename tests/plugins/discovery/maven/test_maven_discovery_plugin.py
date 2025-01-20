"""Unit tests for the Maven discovery plugin."""

import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugins.discovery.maven import MavenDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def test_maven_discovery_plugin_found():
    """Test that the plugin manager finds the Maven discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "maven" for _, plugin in list(discovery_plugins.items())
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
    """Test that the Maven discovery plugin finds two pom.xml files at the same
    depth."""
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


def test_maven_discovery_plugin_scan_with_exceptions():
    """Test that the Maven discovery plugin finds pom.xml files when exceptions are
    specified."""
    mdp = MavenDiscoveryPlugin()
    package = Package(
        "single_package", os.path.join(os.path.dirname(__file__), "single_package")
    )
    exceptions = Exceptions(
        os.path.join(os.path.dirname(__file__), "valid_exceptions.yaml")
    )
    mdp.scan(package, "level", exceptions)

    assert not package["top_poms"]
    assert not package["all_poms"]
