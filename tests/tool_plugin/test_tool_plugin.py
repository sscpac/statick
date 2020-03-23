"""Tests for statick_tool.tool_plugin."""
import argparse
import os
import stat
import sys
import tempfile

import pytest

from statick_tool.config import Config
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin

try:
    from tempfile import TemporaryDirectory
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from backports.tempfile import (
        TemporaryDirectory,
    )  # pylint: disable=wrong-import-order


def test_tool_plugin_load_mapping_valid():
    """Test that we can load the warnings mapping."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )
    arg_parser.add_argument("--output-directory", dest="output_directory")
    resources = Resources([os.path.join(os.path.dirname(__file__), "good_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {"a": "TST1-NO"}


def test_tool_plugin_load_mapping_invalid():
    """Test that we correctly skip invalid entries."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "bad_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_tool_plugin_load_mapping_missing():
    """Test that we return an empty dict for missing files."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "missing_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_tool_plugin_load_mapping_suffixed():
    """Test that we can load the warnings mapping with a suffix."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix",
        dest="mapping_file_suffix",
        type=str,
        default="experimental",
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "good_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {"b": "TST2-NO"}


def test_tool_plugin_load_mapping_suffixed_fallback():
    """Test that we fall back to the non-suffixed file if we can't find a mapping file with an appropriate suffix."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix",
        dest="mapping_file_suffix",
        type=str,
        default="gibberish",
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "good_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {"a": "TST1-NO"}


def test_tool_plugin_get_user_flags_invalid_level():
    """Test that we return an empty list for invalid levels."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources(
        [os.path.join(os.path.dirname(__file__), "user_flags_config")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags("level2", name="test")
    assert flags == []


def test_tool_plugin_get_user_flags_invalid_tool():
    """Test that we return an empty list for undefined tools."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources(
        [os.path.join(os.path.dirname(__file__), "user_flags_config")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags("level", name="test2")
    assert flags == []


def test_tool_plugin_get_user_flags_no_config():
    """Test that we return an empty list for missing configs."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources(
        [os.path.join(os.path.dirname(__file__), "user_flags_config_missing")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags("level", name="test")
    assert flags == []


def test_tool_plugin_get_user_flags_valid_flags():
    """Test that we return a list of user flags."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources(
        [os.path.join(os.path.dirname(__file__), "user_flags_config")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags("level", name="test")
    assert flags == ["look", "a", "flag"]


def test_tool_plugin_is_valid_executable_valid():
    """Test that is_valid_executable returns True for executable files."""

    # Create an executable file
    with tempfile.NamedTemporaryFile() as tmp_file:
        st = os.stat(tmp_file.name)
        os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
        assert ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_no_exe_flag():
    """
    Test that is_valid_executable returns False for a non-executable file.

    NOTE: any platform which doesn't have executable bits should skip
    this test, since the os.stat call will always say that the file is
    executable
    """

    if sys.platform.startswith("win32"):
        pytest.skip("windows doesn't have executable flags")
    # Create a file
    with tempfile.NamedTemporaryFile() as tmp_file:
        assert not ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_nonexistent():
    """Test that is_valid_executable returns False for a nonexistent file."""
    assert not ToolPlugin.is_valid_executable("nonexistent")


def test_tool_dependencies():
    """Verify that dependencies are reported correctly."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources(
        [os.path.join(os.path.dirname(__file__), "user_flags_config")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    assert tp.get_tool_dependencies() == []


def test_tool_plugin_is_valid_executable_extension_nopathext(monkeypatch):
    """
    Test that is_valid_executable works correctly with .exe appended, no PATHEXT

    is_valid_executable should find the file as created.
    """

    # Monkeypatch the environment to clear PATHEXT
    monkeypatch.delenv("PATHEXT", raising=False)

    # Make a temporary executable
    with tempfile.NamedTemporaryFile(suffix=".exe") as tmp_file:
        st = os.stat(tmp_file.name)
        os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
        assert ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_noextension_nopathext(monkeypatch):
    """
    Test that is_valid_executable works correctly with no extension and no PATHEXT

    is_valid_executable should find the file as created.
    """

    # Monkeypatch the environment to clear PATHEXT
    monkeypatch.delenv("PATHEXT", raising=False)

    # Make a temporary executable
    with tempfile.NamedTemporaryFile() as tmp_file:
        st = os.stat(tmp_file.name)
        os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
        assert ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_extension_pathext(monkeypatch):
    """
    Test that is_valid_executable works correctly with an extension and a set PATHEXT

    is_valid_executable should find the file as created.
    """

    # Monkeypatch the environment to set
    monkeypatch.setenv("PATHEXT", ".exe;.bat")

    # Make a temporary executable
    with tempfile.NamedTemporaryFile(suffix=".exe") as tmp_file:
        st = os.stat(tmp_file.name)
        os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
        assert ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_noextension_pathext(monkeypatch):
    """
    Test that is_valid_executable works correctly with no extension and a set PATHEXT

    is_valid_executable should find the file as created.
    """

    # Monkeypatch the environment to set
    monkeypatch.setenv("PATHEXT", ".exe;.bat")

    # Make a temporary executable
    with tempfile.NamedTemporaryFile() as tmp_file:
        st = os.stat(tmp_file.name)
        os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
        assert ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_wrongextension_pathext(monkeypatch):
    """
    Test that is_valid_executable works correctly with a set PATHEXT and a non-PATHEXT extension.

    is_valid_executable should NOT find the file.
    """

    # Monkeypatch the environment to set
    monkeypatch.setenv("PATHEXT", ".exe;.bat")

    # Make a temporary executable
    with tempfile.NamedTemporaryFile(suffix=".potato") as tmp_file:
        st = os.stat(tmp_file.name)
        os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
        # Get the created file minus the suffix
        no_ext_path, _ = os.path.splitext(tmp_file.name)
        assert not ToolPlugin.is_valid_executable(no_ext_path)


def test_tool_plugin_command_exists_fullpath(monkeypatch):
    """Test that command_exists works correctly (full path given). """

    # Monkeypatch the environment to clear PATHEXT
    monkeypatch.delenv("PATHEXT", raising=False)

    # Make a temporary directory which will be part of the path
    with TemporaryDirectory() as tmp_dir:
        # Make a temporary executable
        with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file:
            st = os.stat(tmp_file.name)
            os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
            assert ToolPlugin.command_exists(tmp_file.name)


def test_tool_plugin_command_exists_shortpath_valid(monkeypatch):
    """Test that command_exists works correctly (only filename given, command is on PATH). """

    # Monkeypatch the environment to clear PATHEXT
    monkeypatch.delenv("PATHEXT", raising=False)

    # Make a temporary directory which will be part of the path
    with TemporaryDirectory() as tmp_dir:
        # Make a temporary executable
        with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file:
            st = os.stat(tmp_file.name)
            os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
            monkeypatch.setenv("PATH", tmp_dir)
            _, tmp_file_name = os.path.split(tmp_file.name)
            assert ToolPlugin.command_exists(tmp_file_name)


def test_tool_plugin_command_exists_shortpath_invalid(monkeypatch):
    """Test that command_exists works correctly (only filename given, command is not on PATH). """

    # Monkeypatch the environment to clear PATHEXT
    monkeypatch.delenv("PATHEXT", raising=False)

    # Make a temporary directory which will be part of the path
    with TemporaryDirectory() as tmp_dir:
        # Make a temporary executable
        with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file:
            st = os.stat(tmp_file.name)
            os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
            _, tmp_file_name = os.path.split(tmp_file.name)
            assert not ToolPlugin.command_exists(tmp_file_name)
