"""Tests for statick_tool.tool_plugin."""
import argparse
import os

from statick_tool.config import Config
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def test_tool_plugin_load_mapping_valid():
    """Test that we can load the warnings mapping."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'good_config')])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {'a': 'TST1-NO'}


def test_tool_plugin_load_mapping_invalid():
    """Test that we correctly skip invalid entries."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'bad_config')])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_tool_plugin_load_mapping_missing():
    """Test that we return an empty dict for missing files."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'missing_config')])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_tool_plugin_get_user_flags_invalid_level():
    """Test that we return an empty list for invalid levels."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level2', name='test')
    assert flags == []


def test_tool_plugin_get_user_flags_invalid_tool():
    """Test that we return an empty list for undefined tools."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level', name='test2')
    assert flags == []


def test_tool_plugin_get_user_flags_no_config():
    """Test that we return an empty list for missing configs."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config_missing')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level', name='test')
    assert flags == []


def test_tool_plugin_get_user_flags_valid_flags():
    """Test that we return a list of user flags."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level', name='test')
    assert flags == ['look', 'a', 'flag']
