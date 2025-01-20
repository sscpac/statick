"""Tests for the resources module."""

import logging
import os
import tempfile
from tempfile import TemporaryDirectory

import statick_tool
from statick_tool.resources import Resources

LOGGER = logging.getLogger(__name__)


def test_resources_init():
    """Test initialization of the resources module.

    Expected results: resources.paths should have the argument directory and the
    directory which resources.py lives in
    """
    with TemporaryDirectory() as tmp_dir:
        resources = Resources([tmp_dir])
        assert resources.paths
        assert resources.paths[0] == tmp_dir
        assert resources.paths[1] == os.path.dirname(statick_tool.resources.__file__)


def test_resources_init_empty():
    """Test initialization of the resources module with an empty paths list.

    Expected results: resources.paths should have the directory which resources.py lives
    in
    """
    resources = Resources([])
    assert resources.paths
    assert resources.paths[0] == os.path.dirname(statick_tool.resources.__file__)


def test_resources_init_invalid(caplog):
    """Test initialization of the resources module with an invalid dir.

    Expected results: resources.paths should have the directory which resources.py lives
    in and should print an error for the invalid directory
    """
    LOGGER.info("Testing now.")
    resources = Resources(["invalid_directory"])
    assert resources.paths
    assert resources.paths[0] == os.path.dirname(statick_tool.resources.__file__)
    assert "Could not find path invalid_directory" in caplog.text.splitlines()[0]


def test_resources_init_file(caplog):
    """Test initialization of the resources module with an file as an arg.

    Expected results: resources.paths should have the directory which resources.py lives
    in and should print an error for the file
    """
    LOGGER.info("Testing now.")
    with tempfile.NamedTemporaryFile() as tmpfile:
        resources = Resources([tmpfile.name])
        assert (
            "{} is not a directory".format(tmpfile.name) in caplog.text.splitlines()[0]
        )

    assert resources.paths
    assert resources.paths[0] == os.path.dirname(statick_tool.resources.__file__)


def test_resources_get_plugin_paths_dirs_exist():
    """Test get_plugin_paths where all dirs exist as expected.

    Expected results: get_plugin_paths should contain all of resources.paths with
    '/plugins' appended
    """
    with TemporaryDirectory() as tmp_dir:
        resources = Resources([tmp_dir])
        os.mkdir(os.path.join(tmp_dir, "plugins"))
        plugin_paths = resources.get_plugin_paths()
        assert plugin_paths[0] == os.path.join(tmp_dir, "plugins")
        assert plugin_paths[1] == os.path.join(
            os.path.dirname(statick_tool.resources.__file__), "plugins"
        )


def test_resources_get_plugin_paths_dirs_dont_exist():
    """Test get_plugin_paths where some dirs don't exist as expected.

    Expected results: get_plugin_paths should contain only the default dir with
    '/plugins' appended
    """
    with TemporaryDirectory() as tmp_dir:
        resources = Resources([tmp_dir])
        plugin_paths = resources.get_plugin_paths()
        assert plugin_paths[0] == os.path.join(
            os.path.dirname(statick_tool.resources.__file__), "plugins"
        )


def test_resources_get_file_exists():
    """Test get_file where the file exists.

    Expected results: The file path is returned
    """
    with TemporaryDirectory() as tmp_dir:
        resources = Resources([tmp_dir])
        os.mkdir(os.path.join(tmp_dir, "rsc"))
        with tempfile.NamedTemporaryFile(dir=os.path.join(tmp_dir, "rsc")) as tmpfile:
            assert resources.get_file(tmpfile.name) == os.path.join(
                tmp_dir, "rsc", tmpfile.name
            )


def test_resources_get_file_doesnt_exist():
    """Test get_file where the file doesn't exist.

    Expected results: None is returned
    """
    with TemporaryDirectory() as tmp_dir:
        resources = Resources([tmp_dir])
        os.mkdir(os.path.join(tmp_dir, "rsc"))
        assert resources.get_file("nope") is None
