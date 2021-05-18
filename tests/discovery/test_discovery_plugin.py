"""Tests for statick_tool.discovery_plugin."""
import contextlib
import os
import subprocess

import mock
import pytest

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.package import Package


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


def test_discovery_plugin_find_files():
    """Test calling find files."""
    dp = DiscoveryPlugin()
    if not dp.file_command_exists():
        pytest.skip("File command does not exist. Skipping test that requires it.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    expected = [
        "CMakeLists.txt",
        "package.xml",
        "test.cpp",
        "test.sh",
    ]
    expected_fullpath = [os.path.join(package.path, filename) for filename in expected]
    expected_file_cmd_out = [fullpath + ": empty\n" for fullpath in expected_fullpath]
    expected_dict = {}
    for i, filename in enumerate(expected):
        expected_dict[expected_fullpath[i]] = {
            "name": filename.lower(),
            "path": expected_fullpath[i],
            "file_cmd_out": expected_file_cmd_out[i].lower(),
        }

    dp.find_files(package)

    assert package._walked  # pylint: disable=protected-access
    assert package.files == expected_dict


def test_discovery_plugin_find_files_multiple():
    """Test that find_files will only walk the path once."""
    dp = DiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package._walked = True  # pylint: disable=protected-access
    expected_dict = {}

    dp.find_files(package)

    assert package._walked  # pylint: disable=protected-access
    assert package.files == expected_dict


def test_discovery_plugin_get_file_cmd_output():
    """Test get_file_cmd_output."""
    dp = DiscoveryPlugin()
    if not dp.file_command_exists():
        pytest.skip("File command does not exist. Skipping test that requires it.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    filepath = os.path.join(package.path, "CMakeLists.txt")
    assert filepath.lower() + ": empty\n" == dp.get_file_cmd_output(filepath)


def test_discovery_plugin_get_file_cmd_output_no_file_cmd():
    """Test get_file_cmd_output when file command does not exist."""
    with modified_environ(PATH=""):
        dp = DiscoveryPlugin()
        package = Package(
            "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
        )
        filepath = os.path.join(package.path, "CMakeLists.txt")
        assert "" == dp.get_file_cmd_output(filepath)


@mock.patch("statick_tool.discovery_plugin.subprocess.check_output")
def test_discovery_plugin_get_file_cmd_output_calledprocess_error(
    mock_subprocess_check_output,
):
    """
    Test what happens when a CalledProcessError is raised.

    Expected result: returned empty string.
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        1, "", output="mocked error"
    )
    dp = DiscoveryPlugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    filepath = os.path.join(package.path, "CMakeLists.txt")
    assert "" == dp.get_file_cmd_output(filepath)


def test_discovery_plugin_file_cmd_exists():
    """Test when file command exists."""
    dp = DiscoveryPlugin()
    if not dp.file_command_exists():
        pytest.skip("File command does not exist. Skipping test that requires it.")
    assert dp.file_command_exists()


def test_discovery_plugin_no_file_cmd():
    """Test when file command does not exist."""
    with modified_environ(PATH=""):
        dp = DiscoveryPlugin()
        assert not dp.file_command_exists()
