"""Unit tests for the Config module."""
import os

from statick_tool.config import Config


def test_config_init():
    """
    Test that the Config module initializes correctly.

    Expected result: parser and pre_parser are initialized
    """
    config = Config(None)
    assert not config.config

    config = Config("not_a_file.yaml")
    assert not config.config

    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)
    assert config.config


def test_config_enabled_plugins():
    """
    Test that the Config module identifies enabled plugins for a given level.

    Expected result: plugins listed in example config file are returned
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    plugins = config.get_enabled_plugins("sei_cert", "tool")
    assert "bandit" in plugins
    assert "clang-tidy" in plugins
    assert "cppcheck" in plugins
    assert "flawfinder" in plugins
    assert "make" in plugins
    assert "perlcritic" in plugins
    assert "spotbugs" in plugins


def test_config_enabled_plugins_inherits():
    """
    Test that the Config module identifies enabled plugins for a given level with inheritance.

    Expected result: plugins listed in example config file are returned
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    plugins = config.get_enabled_plugins("objective_minus_pylint", "tool")
    assert "catkin_lint" in plugins
    assert "clang-tidy" in plugins
    assert "cmakelint" in plugins
    assert "cppcheck" in plugins
    assert "make" in plugins
    assert "pylint" in plugins
    assert "xmllint" in plugins
    assert "yamllint" in plugins


def test_config_enabled_tool_plugins():
    """
    Test that the Config module identifies enabled tool plugins for a given level.

    Expected result: plugins listed in example config file are returned
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    plugins = config.get_enabled_tool_plugins("sei_cert")
    assert "bandit" in plugins
    assert "clang-tidy" in plugins
    assert "cppcheck" in plugins
    assert "flawfinder" in plugins
    assert "make" in plugins
    assert "perlcritic" in plugins
    assert "spotbugs" in plugins


def test_config_enabled_discovery_plugins():
    """
    Test that the Config module identifies enabled discovery plugins for a given level.

    Expected result: plugins listed in example config file are returned
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    plugins = config.get_enabled_discovery_plugins("example")
    assert "cmake" in plugins


def test_config_enabled_reporting_plugins():
    """
    Test that the Config module identifies enabled reporting plugins for a given level.

    Expected result: plugins listed in example config file are returned
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    plugins = config.get_enabled_reporting_plugins("example")
    assert "write_to_file" in plugins


def test_config_get_tool_config():
    """
    Test that the Config module gives correct config for tools.

    Expected result: tool plugin configuration matches config file
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    tool_config = config.get_tool_config("make", "example", "flags")
    assert "-Wall" in tool_config


def test_config_get_discovery_config():
    """
    Test that the Config module gives correct config for discovery.

    Expected result: discovery plugin configuration matches config file
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    discovery_config = config.get_discovery_config("cmake", "example", "flags")
    assert not discovery_config


def test_config_get_reporintg_config():
    """
    Test that the Config module gives correct config for reporting.

    Expected result: reporting plugin configuration matches config file
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(config_file)

    reporting_config = config.get_reporting_config("write_to_file", "example", "flags")
    assert not reporting_config
