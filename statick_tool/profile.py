"""Manages which scan levels are run for packages."""

import yaml


class Profile(object):  # pylint: disable=too-few-public-methods
    """Manages which scan levels are run for packages."""

    def __init__(self, filename):
        """Initialize profile."""
        with open(filename) as fname:
            self.profile = yaml.safe_load(fname)

    def get_package_level(self, package):
        """Get which scan level to use for a given package."""
        if "packages" in self.profile:
            packages_profile = self.profile["packages"]
            if packages_profile and package.name in packages_profile:
                return packages_profile[package.name]
        return self.profile["default"]
