"""Unit tests for the PDDL discovery plugin."""
import contextlib
import os
import sys

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package

from statick_tool.plugins.discovery.pddl import PDDLDiscoveryPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


# From https://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment
@contextlib.contextmanager
def modified_environ(*remove, **update):
    """
    Temporarily updates the ``os.environ`` dictionary in-place.

    The ``os.environ`` dictionary is updated in-place so that the modification
    is sure to work in all situations.

    :param remove: Environment variables to remove.
    :param update: Dictionary of environment variables and values to add/update.
    """
    env = os.environ
    update = update or {}
    remove = remove or []

    # List of environment variables being updated or removed.
    stomped = (set(update.keys()) | set(remove)) & set(env.keys())
    # Environment variables and values to restore on exit.
    update_after = {k: env[k] for k in stomped}
    # Environment variables and values to remove on exit.
    remove_after = frozenset(k for k in update if k not in env)

    try:
        env.update(update)
        [env.pop(k, None) for k in remove]
        yield
    finally:
        env.update(update_after)
        [env.pop(k) for k in remove_after]


def test_pddl_discovery_plugin_found():
    """Test that the plugin manager finds the PDDL discovery plugin."""
    discovery_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.discovery")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        discovery_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "pddl" for _, plugin in list(discovery_plugins.items())
    )


def test_pddl_discovery_plugin_scan_valid():
    """Test that the PDDL discovery plugin finds valid PDDL files."""
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    pdp = PDDLDiscoveryPlugin()
    pdp.scan(package, "level")
    expected_domain = [
        "domain.pddl",
        os.path.join("ignore_this", "ignoreme.pddl"),
    ]
    expected_problem = ["problem.pddl"]
    # We have to add the path to each of the above...yuck
    domain_fullpath = [
        os.path.join(package.path, filename) for filename in expected_domain
    ]
    problem_fullpath = [
        os.path.join(package.path, filename) for filename in expected_problem
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["pddl_domain_src"]) == set(domain_fullpath)
    assert set(package["pddl_problem_src"]) == set(problem_fullpath)


def test_pddl_discovery_plugin_scan_invalid():
    """Test that the PDDL discovery plugin doesn't find non-PDDL files."""
    package = Package(
        "invalid_package", os.path.join(os.path.dirname(__file__), "invalid_package")
    )
    pdp = PDDLDiscoveryPlugin()
    pdp.scan(package, "level")
    assert not package["pddl_domain_src"]


def test_pddl_discovery_plugin_scan_exceptions():
    """Test that the PDDL discovery plugin properly respects exceptions."""
    pdp = PDDLDiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__), "exceptions.yaml"))
    pdp.scan(package, "level", exceptions)
    expected_domain_src = ["domain.pddl"]
    expected_problem_src = ["problem.pddl"]
    # We have to add the path to each of the above...yuck
    expected_domain_fullpath = [
        os.path.join(package.path, filename) for filename in expected_domain_src
    ]
    expected_problem_fullpath = [
        os.path.join(package.path, filename) for filename in expected_problem_src
    ]
    # Neat trick to verify that two unordered lists are the same
    assert set(package["pddl_domain_src"]) == set(expected_domain_fullpath)
    assert set(package["pddl_problem_src"]) == set(expected_problem_fullpath)
