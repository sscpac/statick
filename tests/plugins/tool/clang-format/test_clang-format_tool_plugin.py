"""Unit tests for the clang-format plugin."""

import argparse
import os
import shutil
import subprocess
import sys
from xml.etree import ElementTree

import mock
import pytest

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.clang_format import ClangFormatToolPlugin
from statick_tool.plugins.tool.clang_format_parser import ClangFormatXMLParser
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_clang_format_tool_plugin(
    use_plugin_context=True, binary=None, do_raise=False, issue_per_line=False
):
    """Initialize and return an instance of the clang-format plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--clang-format-bin", dest="clang_format_bin")
    if do_raise:
        arg_parser.add_argument(
            "--clang-format-raise-exception",
            dest="clang_format_raise_exception",
            action="store_false",
        )
    else:
        arg_parser.add_argument(
            "--clang-format-raise-exception",
            dest="clang_format_raise_exception",
            action="store_true",
        )

    if issue_per_line:
        arg_parser.add_argument(
            "--clang-format-issue-per-line",
            dest="clang_format_issue_per_line",
            action="store_false",
        )
    else:
        arg_parser.add_argument(
            "--clang-format-issue-per-line",
            dest="clang_format_issue_per_line",
            action="store_true",
        )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    cftp = ClangFormatToolPlugin()
    if binary is not None:
        plugin_context.args.clang_format_bin = binary
    if use_plugin_context:
        cftp.set_plugin_context(plugin_context)
    return cftp


def test_clang_format_tool_plugin_found():
    """Test that the plugin manager can find the clang-format plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "clang-format" for _, plugin in list(plugins.items())
    )


def test_clang_format_tool_plugin_scan_valid():
    """Integration test: Make sure the clang_format output hasn't changed."""
    cftp = setup_clang_format_tool_plugin(do_raise=True)
    if not cftp.command_exists("clang-format"):
        pytest.skip("Missing clang-format executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Copy the latest clang_format over
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert len(issues) == 1

    cftp = setup_clang_format_tool_plugin()
    issues = cftp.scan(package, "level")
    assert not issues

    if os.path.exists(os.path.join(os.path.expanduser("~"), "_clang-format")):
        os.remove(os.path.join(os.path.expanduser("~"), "_clang-format"))


def test_clang_format_tool_plugin_scan_valid_alternate_config():
    """Test that alternate format configuration file can be used."""
    cftp = setup_clang_format_tool_plugin(do_raise=True)
    if not cftp.command_exists("clang-format"):
        pytest.skip("Missing clang-format executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Make sure no configuration files are present.
    if os.path.exists(os.path.join(os.path.expanduser("~"), "_clang-format")):
        os.remove(os.path.join(os.path.expanduser("~"), "_clang-format"))
    if os.path.exists(os.path.join(os.path.expanduser("~"), ".clang-format")):
        os.remove(os.path.join(os.path.expanduser("~"), ".clang-format"))
    # Copy the latest clang_format over
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), ".clang-format"),
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert len(issues) == 1

    cftp = setup_clang_format_tool_plugin()
    issues = cftp.scan(package, "level")
    assert not issues

    if os.path.exists(os.path.join(os.path.expanduser("~"), "_clang-format")):
        os.remove(os.path.join(os.path.expanduser("~"), "_clang-format"))


def test_clang_format_tool_plugin_scan_no_plugin_context():
    """Test that issues are None when no plugin context is provided."""
    cftp = setup_clang_format_tool_plugin(False)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert not issues


def test_clang_format_tool_plugin_scan_missing_fields():
    """Test that issues are empty when fields are missing from the package."""
    cftp = setup_clang_format_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Issues should be empty until make_targets is added to the package.
    issues = cftp.scan(package, "level")
    assert not issues


def test_clang_format_tool_plugin_scan_missing_config_file():
    """Test that issues are None when configuration file is different."""
    cftp = setup_clang_format_tool_plugin(do_raise=True)
    with open(os.path.join(os.path.expanduser("~"), "_clang-format"), "a") as fin:
        fin.write("invalid entry")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert issues is None


def test_clang_format_tool_plugin_scan_different_binary():
    """Test that issues are None when binary is different."""
    cftp = setup_clang_format_tool_plugin(binary="wrong-binary", do_raise=True)
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert issues is None


def test_clang_format_tool_plugin_scan_custom_version():
    """Test that issues is empty when a custom version is specified."""
    cftp = setup_clang_format_tool_plugin()
    if not cftp.command_exists("cmake"):
        pytest.skip("Can't find CMake, unable to test clang_format plugin")
    elif not cftp.command_exists("clang-format"):
        pytest.skip("Can't find clang-format, unable to test clang_format plugin")
    elif not cftp.command_exists("clang-format-14"):
        pytest.skip("Can't find clang-format-14, unable to test clang_format plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "unit_tests")
    assert not issues


def test_clang_format_tool_plugin_scan_missing_config_file_non_default():
    """Test that issues is empty when configuration file is different."""
    cftp = setup_clang_format_tool_plugin(do_raise=True)
    with open(os.path.join(os.path.expanduser("~"), "_clang-format"), "a") as fin:
        fin.write("invalid entry")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert not issues


def test_clang_format_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of clang_format."""
    cftp = setup_clang_format_tool_plugin()
    output = "valid_package/indents.c\n\
<?xml version='1.0'?>\n\
<replacements xml:space='preserve' incomplete_format='false'>\n\
<replacement offset='12' length='1'>&#10;  </replacement>\n\
</replacements>"
    issues = cftp.parse_tool_output([output], [])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/indents.c"
    assert issues[0].line_number == 0
    assert issues[0].tool == "clang-format"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 1
    assert issues[0].message == "1 replacements"


def test_clang_format_tool_plugin_parse_valid_issue_per_line():
    """Verify that multiple issues are found per file when we ask for an issue per
    line."""
    cftp = setup_clang_format_tool_plugin(issue_per_line=True)
    output = "<?xml version='1.0'?>\n\
<replacements xml:space='preserve' incomplete_format='false'>\n\
<replacement offset='12' length='1'>&#10;  </replacement>\n\
<replacement offset='18' length='2'>&#10;  </replacement>\n\
</replacements>"
    files = []
    files.append(os.path.join(os.path.dirname(__file__), "valid_package", "indents.c"))
    files.append(os.path.join(os.path.dirname(__file__), "valid_package", "indents.h"))
    issues = cftp.parse_tool_output([output], files)
    msg = """Replace
- #include "indents.h"
with
+ #include "in
+   ents.h"
"""
    assert len(issues) == 2
    assert issues[0].filename == files[0]
    assert issues[0].line_number == 1
    assert issues[0].tool == "clang-format"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 1
    assert issues[0].message == msg


def test_clang_format_tool_plugin_parse_valid_issue_per_line_no_replacements():
    """Verify that no issues are found per file when no replacements are found."""
    cftp = setup_clang_format_tool_plugin(issue_per_line=True)
    output = ""
    files = []
    issues = cftp.parse_tool_output([output], files)

    assert not issues


def test_clang_format_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of clang_format."""
    cftp = setup_clang_format_tool_plugin()
    output = "invalid text"
    issues = cftp.parse_tool_output(output, [])
    assert not issues


def test_clang_format_tool_plugin_custom_config_diff():
    """Verify that we can identify a diff between actual and target formats."""
    cftp = setup_clang_format_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    cftp.plugin_context.resources
    # Issues should be empty until make_targets is added to the package.
    issues = cftp.scan(package, "level")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.clang_format.subprocess.check_output"
)
def test_clang_format_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means clang-format
    hit an error).

    Expected result: issues is empty (no raise) or None (raise)
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    cftp = setup_clang_format_tool_plugin()
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = []
    issues = cftp.scan(package, "level")
    assert not issues

    cftp = setup_clang_format_tool_plugin(do_raise=True)
    issues = cftp.scan(package, "level")
    assert issues is None

    if os.path.exists(os.path.join(os.path.expanduser("~"), "_clang-format")):
        os.remove(os.path.join(os.path.expanduser("~"), "_clang-format"))


@mock.patch("statick_tool.plugins.tool.clang_format.open")
def test_clang_format_tool_plugin_scan_oserror_open(mock_open):
    """Test what happens when OSError is raised (usually means clang-format
    configuration is missing).

    Expected result: issues is empty (no raise) or None (raise)
    """
    mock_open.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = []
    issues = cftp.scan(package, "level")
    assert not issues

    cftp = setup_clang_format_tool_plugin(do_raise=True)
    issues = cftp.scan(package, "level")
    assert issues is None


@mock.patch(
    "statick_tool.plugins.tool.clang_format.subprocess.check_output"
)
def test_clang_format_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means clang-format doesn't
    exist).

    Expected result: issues is empty (no raise) or None (raise)
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin()
    shutil.copyfile(
        cftp.plugin_context.resources.get_file("_clang-format"),
        os.path.join(os.path.expanduser("~"), "_clang-format"),
    )
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.c")
    ]
    package["headers"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "indents.h")
    ]
    issues = cftp.scan(package, "level")
    assert not issues

    cftp = setup_clang_format_tool_plugin(do_raise=True)
    issues = cftp.scan(package, "level")
    assert issues is None

    if os.path.exists(os.path.join(os.path.expanduser("~"), "_clang-format")):
        os.remove(os.path.join(os.path.expanduser("~"), "_clang-format"))


@mock.patch("statick_tool.plugins.tool.clang_format.open")
def test_clang_format_tool_plugin_check_configuration_oserror(mock_open):
    """Test what happens when an OSError is raised (usually means diff files don't
    exist).

    Expected result: configuration check is False (no raise) or None (raise)
    """
    mock_open.side_effect = OSError("mocked error")
    cftp = setup_clang_format_tool_plugin()
    check = cftp.check_configuration("clang-format")
    assert not check

    cftp = setup_clang_format_tool_plugin(do_raise=True)
    check = cftp.check_configuration("clang-format")
    assert check is None


def test_clang_format_parser_parse_empty_output():
    """Test that empty XML output gives an empty report."""
    cfp = ClangFormatXMLParser()
    report = cfp.parse_xml_output("", "")
    assert not report


def test_clang_format_parser_line_start():
    """Test that we can find the index of where the line starts."""
    cfp = ClangFormatXMLParser()
    data = ""
    offset = 0
    assert cfp.find_index_of_line_start(data, offset) == 0


def test_clang_format_parser_line_end():
    """Test that we can find the index of where the line ends."""
    cfp = ClangFormatXMLParser()
    data = ""
    offset = 0
    assert cfp.find_index_of_line_end(data, offset) == 0


def test_clang_format_parser_line_number():
    """Test that we can find the line number of an issue."""
    cfp = ClangFormatXMLParser()
    data = ""
    offset = 0
    assert cfp.get_line_number(data, offset) == 1

    data = "\n\n\r"
    offset = 2
    assert cfp.get_line_number(data, offset) == 3

    data = "\r\n\n\r"
    offset = 2
    assert cfp.get_line_number(data, offset) == 3


@mock.patch("statick_tool.plugins.tool.clang_format_parser.ElementTree.fromstring")
def test_clang_format_tool_plugin_scan_element_tree_parse_error(mock_fromstring):
    """Test what happens when an ElementTree.ParseError is raised (usually means clang-
    format hit an error).

    Expected result: issues is empty
    """
    mock_fromstring.side_effect = ElementTree.ParseError(1)
    cfp = ClangFormatXMLParser()
    files = []
    files.append(os.path.join(os.path.dirname(__file__), "valid_package", "indents.c"))
    output = "valid_package/indents.c\n\
<?xml version='1.0'?>\n\
<replacements xml:space='preserve' incomplete_format='false'>\n\
<replacement offset='12' length='1'>&#10;  </replacement>\n\
</replacements>"
    issues = cfp.parse_xml_output(output, files)

    assert not issues
