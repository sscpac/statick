"""Tests for the resources module."""

import os
import shutil
import tempfile

import statick_tool
from statick_tool.resources import Resources


def test_resources_init():
    """
    Test initialization of the resources module.

    Expected results: resources.paths should have the argument directory and the directory
    which resources.py lives in
    """
    temp_dir = tempfile.mkdtemp()
    resources = Resources([temp_dir])
    assert resources.paths
    assert resources.paths[0] == temp_dir
    assert resources.paths[1] == os.path.dirname(statick_tool.resources.__file__)
    # Cleanup
    os.rmdir(temp_dir)


def test_resources_init_empty():
    """
    Test initialization of the resources module with an empty paths list.

    Expected results: resources.paths should have the directory which resources.py lives in
    """
    resources = Resources([])
    assert resources.paths
    assert resources.paths[0] == os.path.dirname(statick_tool.resources.__file__)


def test_resources_init_invalid(capsys):
    """
    Test initialization of the resources module with an invalid dir.

    Expected results: resources.paths should have the directory which resources.py lives in
    and should print an error for the invalid directory
    """
    resources = Resources(['invalid_directory'])
    output = capsys.readouterr().out
    assert resources.paths
    assert resources.paths[0] == os.path.dirname(statick_tool.resources.__file__)
    assert output.splitlines()[0] == "Could not find path invalid_directory"


def test_resources_init_file(capsys):
    """
    Test initialization of the resources module with an file as an arg.

    Expected results: resources.paths should have the directory which resources.py lives in
    and should print an error for the file
    """

    with tempfile.NamedTemporaryFile() as tmpfile:
        resources = Resources([tmpfile.name])
        output = capsys.readouterr().out
        assert output.splitlines()[0] == "{} is not a directory".format(tmpfile.name)
    assert resources.paths
    assert resources.paths[0] == os.path.dirname(statick_tool.resources.__file__)


def test_resources_get_plugin_paths_dirs_exist():
    """
    Test get_plugin_paths where all dirs exist as expected

    Expected results: get_plugin_paths should contain all of resources.paths with
    '/plugins' appended
    """
    temp_dir = tempfile.mkdtemp()
    resources = Resources([temp_dir])
    os.mkdir(os.path.join(temp_dir, 'plugins'))
    plugin_paths = resources.get_plugin_paths()
    assert plugin_paths[0] == os.path.join(temp_dir, 'plugins')
    assert plugin_paths[1] == os.path.join(os.path.dirname(
                                           statick_tool.resources.__file__), 'plugins')
    shutil.rmtree(temp_dir)


def test_resources_get_plugin_paths_dirs_dont_exist():
    """
    Test get_plugin_paths where some dirs don't exist as expected

    Expected results: get_plugin_paths should contain only the default dir with
    '/plugins' appended
    """
    temp_dir = tempfile.mkdtemp()
    resources = Resources([temp_dir])
    plugin_paths = resources.get_plugin_paths()
    assert plugin_paths[0] == os.path.join(os.path.dirname(
                                           statick_tool.resources.__file__), 'plugins')
    shutil.rmtree(temp_dir)


def test_resources_get_file_exists():
    """
    Test get_file where the file exists.

    Expected results: The file path is returned
    """
    temp_dir = tempfile.mkdtemp()
    resources = Resources([temp_dir])
    os.mkdir(os.path.join(temp_dir, 'rsc'))
    with tempfile.NamedTemporaryFile(dir=os.path.join(temp_dir, 'rsc')) as tmpfile:
        assert resources.get_file(tmpfile.name) == os.path.join(temp_dir, 'rsc', tmpfile.name)

    shutil.rmtree(temp_dir)


def test_resources_get_file_doesnt_exist():
    """
    Test get_file where the file doesn't exist

    Expected results: None is returned
    """
    temp_dir = tempfile.mkdtemp()
    resources = Resources([temp_dir])
    os.mkdir(os.path.join(temp_dir, 'rsc'))
    assert resources.get_file('nope') is None

    shutil.rmtree(temp_dir)
