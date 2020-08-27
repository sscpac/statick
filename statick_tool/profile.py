"""Manages which scan levels are run for packages."""

from typing import Any, Union

import yaml

from statick_tool.package import Package


class Profile:  # pylint: disable=too-few-public-methods
    """Manages which scan levels are run for packages."""

    def __init__(self, filename: str) -> None:
        """Initialize profile."""
        if not filename:
            raise ValueError("{} is not a valid file".format(filename))
        with open(filename) as fname:
            try:
                self.profile = yaml.safe_load(fname)
            except yaml.YAMLError as ex:
                raise ValueError(
                    "{} is not a valid YAML file: {}".format(filename, ex)
                ) from ex
            if self.profile is None:
                raise ValueError("{} is empty, can't continue!".format(filename))
            if "default" not in self.profile:
                raise ValueError("No 'default' key found in {}!".format(filename))

    def get_package_level(self, package: Package) -> Union[str, Any]:
        """Get which scan level to use for a given package."""
        if "packages" in self.profile:
            packages_profile = self.profile["packages"]
            if packages_profile and package.name in packages_profile:
                return packages_profile[package.name]
        return self.profile["default"]
