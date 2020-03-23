"""Package interface."""


class Package(dict):
    """Default implementation of package interface."""

    def __init__(  # pylint:disable=super-init-not-called
        self, name: str, path: str
    ) -> None:
        """Initialize package interface."""
        self.name = name
        self.path = path
