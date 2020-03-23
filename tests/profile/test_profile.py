"""Unit tests for the Args module."""
import os

import pytest

from statick_tool.package import Package
from statick_tool.profile import Profile


def test_profile_init():
    """
    Test that the Profile module initializes correctly.

    Expected result: profile is initialized
    """
    profile = Profile(os.path.join(os.path.dirname(__file__), "profile.yaml"))
    assert profile.profile


def test_profile_nonexistent():
    """
    Test for when a Profile is initialized with a nonexistent YAML.

    Expected result: OSError is thrown
    """
    with pytest.raises(OSError):
        Profile(os.path.join(os.path.dirname(__file__), "nope.yaml"))


def test_profile_file_empty_string():
    """
    Test for when a Profile is initialized with an empty string.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Profile(os.path.join(""))


def test_profile_empty():
    """
    Test for when a Profile is initialized with an empty YAML.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Profile(os.path.join(os.path.dirname(__file__), "empty.yaml"))


def test_profile_nodefault():
    """
    Test for when a Profile is initialized with a YAML that doesn't have a 'default' key.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Profile(os.path.join(os.path.dirname(__file__), "nodefault.yaml"))


def test_profile_bad_yaml():
    """
    Test for when a Profile is initialized with something that isn't a valid YAML file.

    Expected result: ValueError is thrown
    """
    with pytest.raises(ValueError):
        Profile(os.path.join(os.path.dirname(__file__), "bad.yaml"))


def test_profile_get_package_level_nopackage():
    """
    Test for when get_package_level is called with no packages defined.

    Expected result: default is returned
    """
    package = Package("test", os.path.dirname(__file__))
    profile = Profile(os.path.join(os.path.dirname(__file__), "profile-nopackage.yaml"))
    assert profile.get_package_level(package) == "default_value"


def test_profile_get_package_level_invalidpackage():
    """
    Test for when get_package_level is called with a package not in the packages list.

    Expected result: default is returned
    """
    package = Package("nopackage", os.path.dirname(__file__))
    profile = Profile(os.path.join(os.path.dirname(__file__), "profile.yaml"))
    assert profile.get_package_level(package) == "default_value"


def test_profile_get_package_level_validpackage():
    """
    Test for when get_package_level is called with a package not in the packages list.

    Expected result: the package-specific value is returned
    """
    package = Package("package", os.path.dirname(__file__))
    profile = Profile(os.path.join(os.path.dirname(__file__), "profile.yaml"))
    assert profile.get_package_level(package) == "package_specific"
