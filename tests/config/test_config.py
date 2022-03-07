"""Unit tests for the Config module."""
import os

import mock
import pytest
import yaml

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


def test_config_file_invalid_yaml():
    """
    Test for when a Config is initialized with an invalid yaml file.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Config(os.path.join(os.path.dirname(__file__), "rsc", "bad.yaml"))


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


def test_config_inherits_from_multiple_levels():
    """
    Test that the Config module supports a level that inherits from multiple child levels.

    Expected result: plugins listed in combined config file are returned
    """
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config-list.yaml")
    config = Config(config_file)

    plugins = config.get_enabled_plugins("combined", "discovery")
    assert "C" in plugins
    assert "python" in plugins

    plugins = config.get_enabled_plugins("combined", "tool")
    assert "catkin_lint" in plugins
    assert "cppcheck" in plugins
    assert "cpplint" in plugins
    assert "black" in plugins
    assert "docformatter" in plugins
    assert "isort" in plugins
    assert "mypy" in plugins
    assert "pydocstyle" in plugins
    assert "xmllint" in plugins
    assert "yamllint" in plugins

    plugins = config.get_enabled_plugins("combined", "reporting")
    assert "print_to_console" in plugins
    assert "write_jenkins_warnings_ng" in plugins


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


def test_add_user_config():
    """Test that the Config module adds user levels that inherit from base levels."""
    base_config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    user_config_file = os.path.join(os.path.dirname(__file__), "rsc", "user.yaml")

    config = Config(base_config_file, user_config_file)

    flags = config.get_tool_config("catkin_lint", "custom", "flags")
    assert flags == "--unit_test"

    flags = config.get_tool_config("make", "custom", "flags")
    assert "-Wall" in flags


def test_user_level_overrides_base_level():
    """Test that user level overrides base level in configuration."""
    base_config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    user_config_file = os.path.join(
        os.path.dirname(__file__), "rsc", "user-override.yaml"
    )

    config = Config(base_config_file, user_config_file)

    flags = config.get_tool_config("pylint", "sei_cert", "flags")
    assert flags == "--user-override"

    flags = config.get_tool_config("make", "sei_cert", "flags")
    assert flags is None


def test_user_level_extends_override_level():
    """Test that user level extends a level that overrides a base level."""
    base_config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    user_config_file = os.path.join(
        os.path.dirname(__file__), "rsc", "user-extend.yaml"
    )

    config = Config(base_config_file, user_config_file)

    flags = config.get_tool_config("pylint", "sei_cert", "flags")
    assert flags == "--user-override"

    flags = config.get_tool_config("make", "sei_cert", "flags")
    assert "-Wall" in flags


def test_user_level_override_base_level_with_same_name():
    """Test that user level that overrides a base level with same name finds flags.."""
    base_config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    user_config_file = os.path.join(
        os.path.dirname(__file__), "rsc", "user-level-same-name.yaml"
    )

    config = Config(base_config_file, user_config_file)

    flags = config.get_tool_config("pylint", "threshold", "flags")
    assert flags == "--user-override"

    flags = config.get_tool_config("make", "threshold", "flags")
    assert flags is None


def test_get_config_from_missing_file():
    """Test that None is returned when the configuration file does not exist."""
    base_config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")
    config = Config(base_config_file)
    config_from_file = config.get_config_from_file("")

    assert config_from_file is None


@mock.patch("statick_tool.config.open")
def test_user_config_value_error(mock_open):
    """Test the behavior when Config base file throws a YAMLError."""
    config_file = os.path.join(os.path.dirname(__file__), "rsc", "config.yaml")

    mock_open.side_effect = yaml.YAMLError("error")
    with pytest.raises(yaml.YAMLError):
        Config(config_file)


@mock.patch("statick_tool.config.open")
def test_get_user_levels_value_error(mock_open):
    """Test the behavior when Config user file throws a YAMLError."""
    user_config_file = os.path.join(os.path.dirname(__file__), "rsc", "user.yaml")

    config = Config("")
    mock_open.side_effect = yaml.YAMLError("error")
    with pytest.raises(yaml.YAMLError):
        config.get_user_levels(user_config_file)
