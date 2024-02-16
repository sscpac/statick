"""Tests for statick_tool.reporting_plugin."""

import argparse
import os

from statick_tool.plugin_context import PluginContext
from statick_tool.reporting_plugin import ReportingPlugin
from statick_tool.resources import Resources


def test_reporting_plugin_load_mapping_valid():
    """Test that we can load the warnings mapping."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )
    arg_parser.add_argument("--output-directory", dest="output_directory")
    resources = Resources([os.path.join(os.path.dirname(__file__), "good_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ReportingPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {"a": "TST1-NO"}


def test_reporting_plugin_load_mapping_invalid():
    """Test that we correctly skip invalid entries."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "bad_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ReportingPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_reporting_plugin_load_mapping_missing():
    """Test that we return an empty dict for missing files."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "missing_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ReportingPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_reporting_plugin_load_mapping_suffixed():
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
    tp = ReportingPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {"b": "TST2-NO"}


def test_reporting_plugin_load_mapping_suffixed_fallback():
    """Test that we fall back to the non-suffixed file if we can't find a mapping file
    with an appropriate suffix."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--mapping-file-suffix",
        dest="mapping_file_suffix",
        type=str,
        default="gibberish",
    )
    resources = Resources([os.path.join(os.path.dirname(__file__), "good_config")])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ReportingPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {"a": "TST1-NO"}
