"""Unit tests for the Exceptions module."""
import os

import pytest

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


def test_exceptions_init_valid():
    """
    Test that the Exceptions module initializes correctly.

    Expected result: exceptions.exceptions is initialized.
    """
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__),
                                         'valid_exceptions.yaml'))
    assert exceptions.exceptions


def test_exceptions_init_nonexistent():
    """
    Test that the Exceptions module throws an IOError if a bad path is given.

    Expected result: IOError thrown.
    """
    with pytest.raises(IOError):
        Exceptions(os.path.join(os.path.dirname(__file__),
                                'nonexistent_exceptions.yaml'))


def test_filter_file_exceptions_early():
    """
    Test that filter_file_exceptions_early excludes files.

    Expected result: Empty files list.
    """
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__),
                                         'early_exceptions.yaml'))

    package = Package('test',  os.path.dirname(__file__))
    files = [os.path.join(os.path.dirname(__file__),
                          'unlikelystring')]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert not filtered_files


def test_filter_file_exceptions_early_onlyall():
    """
    Test that filter_file_exceptions_early only uses exceptions with tools=all.

    Expected result: No change to the files list
    """
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__),
                                         'early_exceptions.yaml'))

    package = Package('test',  os.path.dirname(__file__))
    files = [os.path.join(os.path.dirname(__file__),
                          'uncommontext')]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert filtered_files == files


def test_filter_file_exceptions_early_dupes():
    """
    Test that filter_file_exceptions_early excludes duplicated files.

    I have no idea why one might have duplicate files, but might as well test it!
    Expected result: Empty file list.
    """
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__),
                                         'early_exceptions.yaml'))

    package = Package('test',  os.path.dirname(__file__))
    files = [os.path.join(os.path.dirname(__file__),
                          'unlikelystring'),
             os.path.join(os.path.dirname(__file__),
                          'unlikelystring')]

    filtered_files = exceptions.filter_file_exceptions_early(package, files)

    assert not filtered_files
