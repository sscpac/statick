"""Package interface."""


class Package(dict):
    """Default implementation of package interface."""

    def __init__(self, name, path):  # pylint:disable=super-init-not-called
        """Initialize package interface."""
        self.name = name
        self.path = path
