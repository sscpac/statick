"""Unit tests for the Exceptions module."""
import os

import pytest

from statick_tool.exceptions import Exceptions


def test_exceptions_init_valid():
    """
    Test that the Exceptions module initializes correctly.

    Expected result: exceptions.exceptions is initialized
    """
    exceptions = Exceptions(os.path.join(os.path.dirname(__file__),
                                         'valid_exceptions.yaml'))
    assert exceptions.exceptions


def test_exceptions_init_nonexistent():
    """
    Test that the Exceptions module throws an IOError if a bad path is given

    Expected result: IOError thrown
    """
    with pytest.raises(IOError):
        Exceptions(os.path.join(os.path.dirname(__file__),
                                'nonexistent_exceptions.yaml'))
