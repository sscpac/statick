"""Package interface."""


class Package(dict):  # type: ignore
    """Default implementation of package interface."""

    def __init__(  # pylint:disable=super-init-not-called
        self, name: str, path: str
    ) -> None:
        """Initialize package interface.

        Args:
            name: Name of package.
            path: Path to package.
        """
        self.name = name
        self.path = path
        self.files: dict[str, dict[str, str]] = {}
        self._walked = False
