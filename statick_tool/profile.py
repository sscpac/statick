"""
Manages which scan levels are run for packages.
"""
import yaml

class Profile(object):
    """
    Manages which scan levels are run for packages.
    """
    def __init__(self, filename):
        with open(filename) as f:
            self.profile = yaml.safe_load(f)

    def get_package_level(self, package):
        """
        Get which scan level to use for a given package.
        """
        if "packages" in self.profile:
            packages_profile = self.profile["packages"]
            if packages_profile and package.name in packages_profile:
                return packages_profile[package.name]
        return self.profile["default"]
